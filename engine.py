import functools
import logging
import operator
from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Union, TypeVar
from unittest import result

import pandas as pd

from logging_config import IndentLogger

logger = IndentLogger(logging.getLogger('service'))

T = TypeVar('T')


@dataclass
class TypeSpec:
    """Specification for value types"""
    unit: Optional[str] = None
    precision: Optional[int] = None
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None

    def enforce(self, value: Any) -> Any:
        """Enforce type specifications on a value"""
        if value is None:
            return value

        # Convert to numeric if needed
        if isinstance(value, str):
            try:
                value = float(value)
            except ValueError:
                return value

        if not isinstance(value, (int, float)):
            return value

        # Apply min/max constraints
        if self.min is not None:
            value = max(value, self.min)
        if self.max is not None:
            value = min(value, self.max)

        # Apply precision
        if self.precision is not None:
            value = round(value, self.precision)

        # Convert to int for cent units
        if self.unit == 'eurocent':
            value = int(value)

        return value


class AbstractServiceProvider(ABC):
    """Abstract base class for service providers"""

    @abstractmethod
    def __init__(self, reference_date: str):
        pass

    @abstractmethod
    async def get_value(self, service: str, law: str, field: str, temporal: Dict[str, Any],
                        context: Dict[str, Any], overwrite_input: Dict[str, Any]) -> Any:
        pass


@dataclass
class PathNode:
    """Node for tracking evaluation path"""
    type: str
    name: str
    result: Any
    details: Dict[str, Any] = field(default_factory=dict)
    children: List['PathNode'] = field(default_factory=list)


@dataclass
class RuleContext:
    """Context for rule evaluation"""
    definitions: Dict[str, Any]
    service_provider: Optional[AbstractServiceProvider]
    parameters: Dict[str, Any]
    property_specs: Dict[str, Dict[str, Any]]
    output_specs: Dict[str, TypeSpec]
    sources: Dict[str, pd.DataFrame]
    local: Dict[str, Any] = field(default_factory=dict)
    accessed_paths: Set[str] = field(default_factory=set)
    values_cache: Dict[str, Any] = field(default_factory=dict)
    path: List[PathNode] = field(default_factory=list)
    overwrite_input: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    calculation_date: Optional[str] = None

    def track_access(self, path: str):
        """Track accessed data paths"""
        self.accessed_paths.add(path)

    def add_to_path(self, node: PathNode):
        """Add node to evaluation path"""
        if self.path:
            self.path[-1].children.append(node)
        self.path.append(node)

    def pop_path(self):
        """Remove last node from path"""
        if self.path:
            self.path.pop()

    async def resolve_value(self, path: str) -> Any:
        """Resolve a value from definitions, services, or sources"""

        with logger.indent_block(f"Resolving {path}"):

            if not isinstance(path, str) or not path.startswith('$'):
                return path

            path = path[1:]  # Remove $ prefix
            self.track_access(path)

            if path == "calculation_date":
                return self.calculation_date

            # Check local scope first
            if path in self.local:
                logger.debug(f"Resolving from LOCAL: {self.local[path]}")
                return self.local[path]

            # Check definitions first
            if path in self.definitions:
                logger.debug(f"Resolving from DEFINITION: {self.definitions[path]}")
                return self.definitions[path]

            # Check parameters
            if path in self.parameters:
                logger.debug(f"Resolving from PARAMETERS: {self.parameters[path]}")
                return self.parameters[path]

            # Check outputs
            if path in self.outputs:
                logger.debug(f"Resolving from previous OUTPUT: {self.outputs[path]}")
                return self.outputs[path]

            # Check cache
            if path in self.values_cache:
                logger.debug(f"Resolving from CACHE: {self.values_cache[path]}")
                return self.values_cache[path]

            # Check overwrite data
            service_field_key = None
            if path in self.property_specs:
                spec = self.property_specs[path]
                service_ref = spec.get('service_reference', {})
                if service_ref:
                    service_field_key = f"@{service_ref['service']}.{service_ref['field']}"

            if service_field_key and service_field_key in self.overwrite_input:
                value = self.overwrite_input[service_field_key]
                self.values_cache[path] = value
                logger.debug(f"Resolving from OVERWRITE: {value}")
                return value

            # Check sources
            if path in self.property_specs:
                spec = self.property_specs[path]
                source_ref = spec.get('source_reference', {})
                if source_ref and self.sources:
                    table = source_ref.get('table')
                    if table in self.sources:
                        result = await self._resolve_from_source(source_ref, table)
                        self.values_cache[path] = result
                        logger.debug(f"Resolving from SOURCE {table}: {result}")
                        return result

            # Check services
            if path in self.property_specs:
                spec = self.property_specs[path]
                service_ref = spec.get('service_reference', {})
                if service_ref and self.service_provider:
                    value = await self._resolve_from_service(service_ref, spec)
                    self.values_cache[path] = value
                    logger.debug(
                        f"Result for ${path} from {service_ref['service']} field {service_ref['field']}: {value}")
                    return value
            logger.warning(f"Could not resolve value for {path}")
            return None

    async def _resolve_from_service(self, service_ref, spec):
        parameters = copy(self.parameters)
        if 'parameters' in service_ref:
            parameters.update({p['name']: await self.resolve_value(p['reference'])
                               for p in service_ref['parameters']})
        logger.debug(
            f"Resolving from {service_ref['service']} field {service_ref['field']} ({parameters})")
        value = await self.service_provider.get_value(
            service_ref['service'],
            service_ref['law'],
            service_ref['field'],
            spec['temporal'],
            parameters,
            self.overwrite_input
        )
        return value

    async def _resolve_from_source(self, source_ref, table):
        df = self.sources[table]

        # Filter
        if 'select_on' in source_ref:
            for select_on in source_ref['select_on']:
                value = await self.resolve_value(select_on['value'])

                if isinstance(value, dict) and 'operation' in value and value['operation'] == 'IN':
                    allowed_values = await self.resolve_value(value['values'])
                    df = df[df[select_on['name']].isin(allowed_values)]
                else:
                    df = df[df[select_on['name']] == value]

        # Get specified fields
        fields = source_ref.get('fields', [])
        field = source_ref.get('field')

        if fields:
            missing_fields = [f for f in fields if f not in df.columns]
            if missing_fields:
                logger.warning(f"Fields {missing_fields} not found in source for table {table}")
            existing_fields = [f for f in fields if f in df.columns]
            result = df[existing_fields].to_dict('records')
        elif field:
            if field not in df.columns:
                logger.warning(f"Field {field} not found in source for table {table}")
                return None
            result = df[field].tolist()
        else:
            result = df.to_dict('records')

        if result is None:
            return None
        if len(result) == 0:
            return None
        if len(result) == 1:
            return result[0]
        return result


class RulesEngine:
    """Rules engine for evaluating business rules"""

    def __init__(self, spec: Dict[str, Any], service_provider: Optional[AbstractServiceProvider] = None):
        self.spec = spec
        self.service_name = spec.get('service')
        self.law = spec.get('law')
        self.definitions = spec.get('properties', {}).get('definitions', {})
        self.requirements = spec.get('requirements', [])
        self.actions = spec.get('actions', [])
        self.property_specs = self._build_property_specs(spec.get('properties', {}))
        self.output_specs = self._build_output_specs(spec.get('properties', {}))
        self.service_provider = service_provider

    @staticmethod
    def _build_property_specs(properties: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Build mapping of property paths to their specifications"""
        specs = {}

        # Add input properties
        for prop in properties.get('input', []):
            if 'name' in prop:
                specs[prop['name']] = prop

        # Add source properties
        for source in properties.get('sources', []):
            if 'name' in source:
                specs[source['name']] = source

        return specs

    @staticmethod
    def _build_output_specs(properties: Dict[str, Any]) -> Dict[str, TypeSpec]:
        """Build mapping of output names to their type specifications"""
        specs = {}
        for output in properties.get('output', []):
            if 'name' in output:
                type_spec = output.get('type_spec', {})
                specs[output['name']] = TypeSpec(
                    unit=type_spec.get('unit'),
                    precision=type_spec.get('precision'),
                    min=type_spec.get('min'),
                    max=type_spec.get('max')
                )
        return specs

    def _enforce_output_type(self, name: str, value: Any) -> Any:
        """Enforce type specifications on output value"""
        if name in self.output_specs:
            return self.output_specs[name].enforce(value)
        return value

    async def evaluate(self, parameters: Optional[Dict[str, Any]] = None,
                       overwrite_input: Optional[Dict[str, Any]] = None,
                       sources: Dict[str, pd.DataFrame] = None,
                       calculation_date=None, requested_output: str = None) -> Dict[str, Any]:
        """Evaluate rules using service context and sources
        :param calculation_date:
        """
        logger.debug(f"Evaluating rules for {self.service_name} {self.law} ({calculation_date} {requested_output})")
        root = PathNode(type='root', name='evaluation', result=None)
        context = RuleContext(
            definitions=self.definitions,
            service_provider=self.service_provider,
            parameters=parameters or {},
            property_specs=self.property_specs,
            output_specs=self.output_specs,
            sources=sources,
            path=[root],
            overwrite_input=overwrite_input or {},
            calculation_date=calculation_date,
        )

        # Check requirements
        requirements_node = PathNode(type='requirements', name='Check all requirements', result=None)
        context.add_to_path(requirements_node)
        requirements_met = await self._evaluate_requirements(self.requirements, context)
        requirements_node.result = requirements_met
        context.pop_path()

        input_values = dict(context.values_cache)
        output_values = {}

        if requirements_met:
            for action in self.actions:
                output_name = action['output']
                if requested_output and requested_output != output_name:
                    logger.debug(f"Skipping action {output_name}")
                    continue
                output_def, output_name = await self._evaluate_action(action, context)
                context.outputs[output_name] = output_def['value']
                output_values[output_name] = output_def
                context.pop_path()

        return {
            'input': input_values,
            'output': output_values,
            'requirements_met': requirements_met,
            'path': root
        }

    async def _evaluate_action(self, action, context):
        with logger.indent_block(f"Computing {action.get('output', '')}"):
            action_node = PathNode(
                type='action',
                name=f"Evaluate action for {action.get('output', '')}",
                result=None
            )
            context.add_to_path(action_node)
            output_name = action['output']
            # Find output specification
            output_spec = next((
                spec for spec in self.spec.get('properties', {}).get('output', [])
                if spec.get('name') == output_name
            ), {})
            # Check for overwrite using service name
            service_path = f"@{self.service_name}.{output_name}"
            if service_path in context.overwrite_input:
                raw_result = context.overwrite_input[service_path]
                logger.debug(f"Resolving value {service_path} from OVERWRITE {raw_result}")
            elif 'value' in action:
                raw_result = await self._evaluate_value(action['value'], context)
            else:
                raw_result = await self._evaluate_operation(action, context)
            result = self._enforce_output_type(output_name, raw_result)
        action_node.result = result
        logger.debug(f"Result of {action.get('output', '')}: {result}")
        # Build output with metadata
        output_def = {
            'value': result,
            'type': output_spec.get('type', 'unknown'),
            'description': output_spec.get('description', '')
        }
        # Add type_spec if present
        if 'type_spec' in output_spec:
            output_def['type_spec'] = output_spec['type_spec']
        # Add temporal if present
        if 'temporal' in output_spec:
            output_def['temporal'] = output_spec['temporal']
        return output_def, output_name

    async def _evaluate_requirements(self, requirements: list, context: RuleContext) -> bool:
        """Evaluate all requirements"""
        if not requirements:
            logger.debug("No requirements found")
            return True

        for req in requirements:
            with logger.indent_block(f"Requirements {req}"):
                node = PathNode(type='requirement',
                                name='Check ALL conditions' if 'all' in req else 'Check OR conditions' if 'or' in req else 'Test condition',
                                result=None)
                context.add_to_path(node)

                if 'all' in req:
                    results = []
                    for r in req['all']:
                        result = await self._evaluate_requirements([r], context)
                        results.append(result)
                    result = all(results)
                elif 'or' in req:
                    results = []
                    for r in req['or']:
                        result = await self._evaluate_requirements([r], context)
                        results.append(result)
                    result = any(results)
                else:
                    result = await self._evaluate_operation(req, context)

            logger.debug(f"Requirement met" if {result} else f"Requirement NOT met")

            node.result = result
            context.pop_path()

            if not result:
                return False

        return True

    async def _evaluate_if_operation(self, operation: Dict[str, Any], context: RuleContext) -> Any:
        """Evaluate an IF operation"""
        if_node = PathNode(type='operation',
                           name='IF conditions',
                           result=None,
                           details={'condition_results': []})
        context.add_to_path(if_node)

        result = 0
        conditions = operation.get('conditions', [])

        for i, condition in enumerate(conditions):
            condition_result = {
                'condition_index': i,
                'type': 'test' if 'test' in condition else 'else'
            }

            if 'test' in condition:
                test_result = await self._evaluate_operation(condition['test'], context)
                condition_result['test_result'] = test_result
                if test_result:
                    result = await self._evaluate_value(condition['then'], context)
                    condition_result['then_value'] = result
                    if_node.details['condition_results'].append(condition_result)
                    break
            elif 'else' in condition:
                result = await self._evaluate_value(condition['else'], context)
                condition_result['else_value'] = result
                if_node.details['condition_results'].append(condition_result)
                break

            if_node.details['condition_results'].append(condition_result)

        if_node.result = result
        context.pop_path()
        return result

    async def _evaluate_foreach(self, operation, context):
        """Handle FOREACH operation"""
        combine = operation.get('combine')

        array_data = await self._evaluate_value(operation['subject'], context)
        if not array_data:
            logger.warning("No data found to run FOREACH on")
            return self._evaluate_arithmetic(combine, [])

        if not isinstance(array_data, list):
            array_data = [array_data]

        with logger.indent_block(f"Foreach({combine})"):
            values = []
            for item in array_data:
                with logger.indent_block(f"Item {item}"):
                    item_context = copy(context)
                    item_context.local = item
                    result = await self._evaluate_value(operation['value'][0], item_context)
                    values.extend(result if isinstance(result, list) else [result])
            logger.debug(f"Foreach values: {values}")
            result = self._evaluate_arithmetic(combine, values)
            logger.debug(f"Foreach result: {result}")
        return result

    COMPARISON_OPS = {
        'EQUALS': operator.eq,
        'NOT_EQUALS': operator.ne,
        'GREATER_THAN': operator.gt,
        'LESS_THAN': operator.lt,
        'GREATER_OR_EQUAL': operator.ge,
        'LESS_OR_EQUAL': operator.le,
    }

    ARITHMETIC_OPS = {
        'MIN': min,
        'MAX': max,
        'ADD': sum,
        'MULTIPLY': lambda vals: functools.reduce(
            lambda x, y: int(x * y) if isinstance(y, float) and y < 1 else x * y,
            vals[1:],
            vals[0]
        ),
        'SUBTRACT': lambda vals: functools.reduce(operator.sub, vals[1:], vals[0]),
        'DIVIDE': lambda vals: (
            functools.reduce(
                lambda x, y: x / y if y != 0 else 0,
                vals[1:],
                float(vals[0])
            ) if 0 not in vals[1:] else 0
        )
    }

    @staticmethod
    def _evaluate_arithmetic(op: str, values: List[Any]) -> Union[int, float]:
        """Handle pure arithmetic operations"""
        if not values:
            logger.warning(f"No values found, returning 0 for {op}")
            return 0
        result = RulesEngine.ARITHMETIC_OPS[op](values)
        logger.debug(f"Compute {op}({values}) = {result}")
        return result

    @staticmethod
    def _evaluate_comparison(op: str, left: Any, right: Any) -> bool:
        """Handle comparison operations"""
        if isinstance(left, date) and isinstance(right, str):
            right = datetime.strptime(right, "%Y-%m-%d").date()
        elif isinstance(right, date) and isinstance(left, str):
            left = datetime.strptime(left, "%Y-%m-%d").date()

        result = RulesEngine.COMPARISON_OPS[op](left, right)
        logger.debug(f"Compute {op}({left}, {right}) = {result}")
        return result

    def _evaluate_date_operation(self, op: str, values: List[Any], unit: str) -> int:
        """Handle date-specific operations"""
        result = None
        if op == 'SUBTRACT_DATE':

            if len(values) != 2:
                logger.warning(f"Warning: SUBTRACT_DATE requires exactly 2 values")
                return 0

            end_date, start_date = values

            if not isinstance(end_date, datetime):
                end_date = datetime.fromisoformat(str(end_date))
            if not isinstance(start_date, datetime):
                start_date = datetime.fromisoformat(str(start_date))

            delta = end_date - start_date

            if unit == 'days':
                result = delta.days
            elif unit == 'years':
                result = (end_date.year - start_date.year -
                          ((end_date.month, end_date.day) <
                           (start_date.month, start_date.day)))
            elif unit == 'months':
                result = ((end_date.year - start_date.year) * 12 +
                          end_date.month - start_date.month)
            else:
                logger.warning(f"Warning: Unknown date unit {unit}")
            logger.debug(f"Compute {op}({values}, {unit}) = {result}")

        if result is None:
            logger.warning(f"Warning: date operation resulted in None")

        return result

    async def _evaluate_operation(self, operation: Dict[str, Any], context: RuleContext) -> Any:
        """Evaluate an operation or condition"""

        if not isinstance(operation, dict):
            node = PathNode(
                type='value',
                name="Direct value evaluation",
                result=None,
                details={'raw_value': operation}
            )
            context.add_to_path(node)
            result = await self._evaluate_value(operation, context)
            node.result = result
            context.pop_path()
            return result

        # Direct value assignment - no operation needed
        if 'value' in operation and not operation.get('operation'):
            node = PathNode(
                type='direct_value',
                name="Direct value assignment",
                result=None,
                details={'raw_value': operation['value']}
            )
            context.add_to_path(node)
            result = await self._evaluate_value(operation['value'], context)
            node.result = result
            context.pop_path()
            return result

        op_type = operation.get('operation')
        node = PathNode(
            type='operation',
            name=f"Operation: {op_type}",
            result=None,
            details={'operation_type': op_type}
        )
        context.add_to_path(node)

        if op_type == 'IF':
            result = await self._evaluate_if_operation(operation, context)

        elif op_type == 'FOREACH':
            result = await self._evaluate_foreach(operation, context)
            node.details.update({
                'raw_values': operation['value'],
                'arithmetic_type': op_type
            })

        elif op_type == 'IN':
            with logger.indent_block(f"IN"):

                subject = await self._evaluate_value(operation['subject'], context)
                allowed_values = await self._evaluate_value(operation.get('values', []), context)
                result = subject in (allowed_values if isinstance(allowed_values, list) else [allowed_values])

            node.details.update({
                'subject_value': subject,
                'allowed_values': allowed_values
            })
            logger.debug(f"Result {subject} IN {allowed_values}: {result}")

        elif op_type == 'NOT_NULL':
            subject = await self._evaluate_value(operation['subject'], context)
            result = subject is not None
            node.details['subject_value'] = subject

        elif op_type == 'AND':
            with logger.indent_block(f"AND"):

                values = [await self._evaluate_value(v, context) for v in operation['values']]
                result = all(bool(v) for v in values)

            node.details['evaluated_values'] = values
            logger.debug(f"Result {[v for v in values]} AND: {result}")

        elif op_type == 'OR':
            with logger.indent_block(f"OR"):

                values = [await self._evaluate_value(v, context) for v in operation['values']]
                result = any(bool(v) for v in values)
            node.details['evaluated_values'] = values
            logger.debug(f"Result {[v for v in values]} OR: {result}")

        elif '_DATE' in op_type:
            values = [await self._evaluate_value(v, context) for v in operation['values']]
            unit = operation.get('unit', 'days')
            result = self._evaluate_date_operation(op_type, values, unit)
            node.details.update({
                'evaluated_values': values,
                'unit': unit
            })


        elif op_type in self.COMPARISON_OPS:
            subject = None
            value = None

            # Handle comparison conditions
            if 'subject' in operation:
                subject = await self._evaluate_value(operation['subject'], context)
                value = await self._evaluate_value(operation['value'], context)

            elif 'values' in operation:
                values = [await self._evaluate_value(v, context) for v in operation['values']]
                subject = values[0]
                value = values[1]
            else:
                logger.warning(f"Comparison operation expects two values or subject/value.")

            result = self._evaluate_comparison(op_type, subject, value)

            node.details.update({
                'subject_value': subject,
                'comparison_value': value,
                'comparison_type': op_type
            })

        elif op_type in self.ARITHMETIC_OPS and 'values' in operation:
            # Handle arithmetic operations
            values = [await self._evaluate_value(v, context) for v in operation['values']]
            result = self._evaluate_arithmetic(op_type, values)
            node.details.update({
                'raw_values': operation['values'],
                'evaluated_values': values,
                'arithmetic_type': op_type
            })

        else:
            result = None
            node.details['error'] = 'Invalid operation format'
            logger.warning(f"Not matched to any operation {op_type}")

        node.result = result
        context.pop_path()
        return result

    async def _evaluate_value(self, value: Any, context: RuleContext) -> Any:
        """Evaluate a value which might be a number, operation, or reference"""
        if isinstance(value, (int, float, bool, date, datetime)):
            return value
        elif isinstance(value, dict) and 'operation' in value:
            return await self._evaluate_operation(value, context)
        else:
            return await context.resolve_value(value)
