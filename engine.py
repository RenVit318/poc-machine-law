import functools
import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union, TypeVar

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
                        context: Dict[str, Any]) -> Any:
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
    service_context: Dict[str, Any]
    property_specs: Dict[str, Dict[str, Any]]
    output_specs: Dict[str, Dict[str, Any]]
    sources: Optional[Dict[str, Dict[str, Any]]] = None
    accessed_paths: Set[str] = field(default_factory=set)
    values_cache: Dict[str, Any] = field(default_factory=dict)
    path: List[PathNode] = field(default_factory=list)
    overwrite_input: Dict[str, Any] = field(default_factory=dict)
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
        if not isinstance(path, str) or not path.startswith('$'):
            return path

        path = path[1:]  # Remove $ prefix
        self.track_access(path)

        if path == "calculation_date":
            return self.calculation_date

        # Check definitions first
        if path in self.definitions:
            print(f"        RESOLVING VALUE ${path} FROM DEFINITION {self.definitions[path]}")
            return self.definitions[path]

        # Check cache
        if path in self.values_cache:
            print(f"        RESOLVING VALUE ${path} FROM CACHE {self.values_cache[path]}")
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
            print(f"        RESOLVING VALUE ${path} FROM OVERWRITE {value}")
            return value

        # Check sources
        if path in self.property_specs:
            spec = self.property_specs[path]
            source_ref = spec.get('source_reference', {})
            if source_ref and self.sources:
                table = source_ref.get('table')
                field = source_ref.get('field')
                if table in self.sources and field in self.sources[table]:
                    value = self.sources[table][field]
                    print(f"        RESOLVING VALUE ${path} FROM SOURCE {table} {field}: {value}")
                    self.values_cache[path] = value
                    return value

        # Check services
        if path in self.property_specs:
            spec = self.property_specs[path]
            service_ref = spec.get('service_reference', {})
            if service_ref and self.service_provider:
                value = await self.service_provider.get_value(
                    service_ref['service'],
                    service_ref['law'],
                    service_ref['field'],
                    spec['temporal'],
                    self.service_context
                )
                self.values_cache[path] = value
                print(
                    f"        RESOLVING VALUE ${path} FROM SERVICE {service_ref['service']} field {service_ref['field']} ({self.service_context}): {value}")
                return value

        return None


class RulesEngine:
    """Rules engine for evaluating business rules"""

    def __init__(self, spec: Dict[str, Any], service_provider: Optional[AbstractServiceProvider] = None):
        self.spec = spec
        self.definitions = spec.get('properties', {}).get('definitions', {})
        self.requirements = spec.get('requirements', [])
        self.actions = spec.get('actions', [])
        self.property_specs = self._build_property_specs(spec.get('properties', {}))
        self.output_specs = self._build_output_specs(spec.get('properties', {}))
        self.service_provider = service_provider

    def _build_property_specs(self, properties: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
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

    def _build_output_specs(self, properties: Dict[str, Any]) -> Dict[str, TypeSpec]:
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

    async def evaluate(self, service_context: Optional[Dict[str, Any]] = None,
                       overwrite_input: Optional[Dict[str, Any]] = None,
                       sources: Optional[Dict[str, Dict[str, Any]]] = None,
                       calculation_date=None) -> Dict[str, Any]:
        """Evaluate rules using service context and sources
        :param calculation_date:
        """

        root = PathNode(type='root', name='evaluation', result=None)
        context = RuleContext(
            definitions=self.definitions,
            service_provider=self.service_provider,
            service_context=service_context or {},
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

        # Process actions if requirements are met
        if requirements_met:
            for action in self.actions:
                print(f"    RUNNING ACTION {action.get('output', '')}")
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

                # Get the value
                if 'value' in action:
                    result = self._enforce_output_type(output_name, action['value'])
                    action_node.result = result
                else:
                    raw_result = await self._evaluate_operation(action, context)
                    result = self._enforce_output_type(output_name, raw_result)
                    action_node.result = result

                print(f"        RESULT OF ACTION {action.get('output', '')}: {result}")

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

                output_values[output_name] = output_def
                context.pop_path()

        return {
            'input': input_values,
            'output': output_values,
            'requirements_met': requirements_met,
            'path': root
        }

    async def _evaluate_requirements(self, requirements: list, context: RuleContext) -> bool:
        """Evaluate all requirements"""
        if not requirements:
            return True

        for req in requirements:
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

        try:
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

        except Exception as e:
            print(f"Error evaluating IF operation: {e}")
            context.pop_path()
            return 0

    def _evaluate_arithmetic(self, op: str, values: List[Any]) -> Union[int, float]:
        """Handle pure arithmetic operations"""
        if not values:
            return 0

        ops = {
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
                    lambda x, y: int(x / y) if y != 0 else 0,
                    vals[1:],
                    vals[0]
                ) if 0 not in vals[1:] else 0
            )
        }
        return ops[op](values)

    def _evaluate_comparison(self, op: str, left: Any, right: Any) -> bool:
        """Handle comparison operations"""
        ops = {
            'EQUALS': operator.eq,
            'NOT_EQUALS': operator.ne,
            'GREATER_THAN': operator.gt,
            'LESS_THAN': operator.lt,
            'GREATER_OR_EQUAL': operator.ge,
            'LESS_OR_EQUAL': operator.le,
        }
        return ops[op](left, right)

    def _evaluate_date_operation(self, op: str, values: List[Any], unit: str) -> int:
        """Handle date-specific operations"""
        if op == 'SUBTRACT_DATE':

            if len(values) != 2:
                print(f"Warning: SUBTRACT_DATE requires exactly 2 values")
                return 0

            end_date, start_date = values

            if not isinstance(end_date, datetime):
                end_date = datetime.fromisoformat(str(end_date))
            if not isinstance(start_date, datetime):
                start_date = datetime.fromisoformat(str(start_date))

            delta = end_date - start_date

            if unit == 'days':
                return delta.days
            elif unit == 'years':
                return (end_date.year - start_date.year -
                        ((end_date.month, end_date.day) <
                         (start_date.month, start_date.day)))
            elif unit == 'months':
                return ((end_date.year - start_date.year) * 12 +
                        end_date.month - start_date.month)
            else:
                print(f"Warning: Unknown date unit {unit}")
                return 0

    async def _evaluate_operation(self, operation: Dict[str, Any], context: RuleContext) -> Any:
        """Evaluate an operation or condition"""
        if not isinstance(operation, dict):
            return await self._evaluate_value(operation, context)

        # Direct value assignment - no operation needed
        if 'value' in operation and not operation.get('operation'):
            return await self._evaluate_value(operation['value'], context)

        op_type = operation.get('operation')
        node = PathNode(
            type='operation',
            name=f"Operation: {op_type}",
            result=None,
            details={'operation_type': op_type}
        )
        context.add_to_path(node)

        try:
            if op_type == 'IF':
                result = await self._evaluate_if_operation(operation, context)

            elif op_type == 'IN':
                subject = await self._evaluate_value(operation['subject'], context)
                allowed_values = await self._evaluate_value(operation.get('values', []), context)
                result = subject in (allowed_values if isinstance(allowed_values, list) else [allowed_values])

            elif op_type == 'NOT_NULL':
                subject = await self._evaluate_value(operation['subject'], context)
                result = subject is not None
                node.details['subject_value'] = subject

            elif op_type == 'AND':
                values = [await self._evaluate_value(v, context) for v in operation['values']]
                result = all(bool(v) for v in values)

            elif op_type == 'OR':
                values = [await self._evaluate_value(v, context) for v in operation['values']]
                result = any(bool(v) for v in values)

            elif op_type == 'SUBTRACT_DATE':
                values = [await self._evaluate_value(v, context) for v in operation['values']]
                unit = operation.get('unit', 'days')
                result = self._evaluate_date_operation(op_type, values, unit)

            elif 'subject' in operation:
                # Handle comparison conditions
                subject = await self._evaluate_value(operation['subject'], context)
                value = await self._evaluate_value(operation['value'], context)
                result = self._evaluate_comparison(op_type, subject, value)
                node.details.update({
                    'subject_value': subject,
                    'comparison_value': value
                })

            elif 'values' in operation:
                # Handle arithmetic operations
                values = [await self._evaluate_value(v, context) for v in operation['values']]
                result = self._evaluate_arithmetic(op_type, values)
                node.details.update({
                    'raw_values': operation['values'],
                    'evaluated_values': values
                })

            else:
                result = 0

            node.result = result
            context.pop_path()
            return result

        except Exception as e:
            print(f"Error evaluating operation: {e} ({operation})")
            context.pop_path()
            return 0

    async def _evaluate_value(self, value: Any, context: RuleContext) -> Any:
        """Evaluate a value which might be a number, operation, or reference"""
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, dict) and 'operation' in value:
            return await self._evaluate_operation(value, context)
        else:
            resolved = await context.resolve_value(value)
            return resolved if resolved is not None else 0
