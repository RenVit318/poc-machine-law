import functools
import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


class AbstractServiceProvider(ABC):
    """Abstract base class for service providers"""

    @abstractmethod
    def __init__(self, config_path: str):
        pass

    @abstractmethod
    async def get_value(self, service: str, method: str, context: Dict[str, Any]) -> Any:
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
    accessed_paths: Set[str] = field(default_factory=set)
    values_cache: Dict[str, Any] = field(default_factory=dict)
    path: List[PathNode] = field(default_factory=list)
    overwrite_input: Dict[str, Any] = field(default_factory=dict)

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
        """Resolve a value from definitions or services"""
        if not isinstance(path, str) or not path.startswith('$'):
            return path

        path = path[1:]  # Remove $ prefix
        self.track_access(path)

        # Check definitions first
        if path in self.definitions:
            return self.definitions[path]

        # Check cache
        if path in self.values_cache:
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
            return value

        # Check services
        if path in self.property_specs:
            spec = self.property_specs[path]
            service_ref = spec.get('service_reference', {})
            if service_ref and self.service_provider:
                value = await self.service_provider.get_value(
                    service_ref['service'],
                    service_ref['field'],
                    self.service_context
                )
                self.values_cache[path] = value
                return value

        return None


class RulesEngine:
    """Rules engine for evaluating business rules"""

    def __init__(self, spec: Dict[str, Any], service_provider: Optional[AbstractServiceProvider] = None):
        self.definitions = spec.get('properties', {}).get('definitions', {})
        self.requirements = spec.get('requirements', [])
        self.actions = spec.get('actions', [])
        self.property_specs = self._build_property_specs(spec.get('properties', {}))
        self.service_provider = service_provider

    def _build_property_specs(self, properties: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Build mapping of property paths to their specifications"""
        return {
            prop['name']: prop
            for prop in properties.get('input', [])
            if 'name' in prop
        }

    def _calculate(self, op: str, values: List[Any]) -> Any:
        """Calculate result based on operation type"""
        if not values:
            return 0

        operations = {
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

        return operations.get(op, lambda _: 0)(values)

    def _compare(self, op: str, left: Any, right: Any) -> bool:
        """Compare two values based on operator"""
        ops = {
            'EQUALS': operator.eq,
            'NOT_EQUALS': operator.ne,
            'GREATER_THAN': operator.gt,
            'LESS_THAN': operator.lt,
            'GREATER_OR_EQUAL': operator.ge,
            'LESS_OR_EQUAL': operator.le,
        }
        return ops[op](left, right) if op in ops else False

    async def evaluate(self, service_context: Optional[Dict[str, Any]] = None,
                       overwrite_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Evaluate rules using service context"""
        root = PathNode(type='root', name='evaluation', result=None)
        context = RuleContext(
            definitions=self.definitions,
            service_provider=self.service_provider,
            service_context=service_context or {},
            property_specs=self.property_specs,
            path=[root],
            overwrite_input=overwrite_input or {}
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
                action_node = PathNode(type='action',
                                       name=f"Evaluate action for {action.get('output', '')}",
                                       result=None)
                context.add_to_path(action_node)

                if 'value' in action:
                    output_values[action['output']] = action['value']
                    action_node.result = action['value']
                else:
                    result = await self._evaluate_operation(action, context)
                    output_values[action['output']] = result
                    action_node.result = result

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
                result = await self._evaluate_condition(req, context)

            node.result = result
            context.pop_path()

            if not result:
                return False

        return True

    async def _evaluate_condition(self, condition: Dict[str, Any], context: RuleContext) -> bool:
        """Evaluate a single condition"""
        test_desc = f"Test: {condition.get('subject', 'operation')}"
        node = PathNode(type='test', name=test_desc, result=None, details={})
        context.add_to_path(node)

        try:
            if 'operation' in condition:
                values = [await self._evaluate_value(v, context) for v in condition['values']]
                result = self._compare(condition['operation'], *values)
                node.details.update({
                    'operation': condition['operation'],
                    'values': values
                })
            else:
                subject = await self._evaluate_value(condition['subject'], context)
                value = await self._evaluate_value(condition['value'], context)
                result = self._compare(condition['operator'], subject, value)
                node.details.update({
                    'subject_path': condition['subject'],
                    'subject_value': subject,
                    'operator': condition['operator'],
                    'comparison_value': value
                })

            node.result = result
            context.pop_path()
            return result

        except Exception as e:
            print(f"Error evaluating condition: {e}")
            context.pop_path()
            return False

    async def _evaluate_operation(self, operation: Dict[str, Any], context: RuleContext) -> Any:
        """Evaluate an operation"""
        if not isinstance(operation, dict):
            return await self._evaluate_value(operation, context)

        op_type = operation.get('operation')
        node = PathNode(type='operation',
                        name=f"Operation: {op_type}",
                        result=None,
                        details={'operation_type': op_type})
        context.add_to_path(node)

        try:
            if op_type == 'IF':
                result = await self._evaluate_if_operation(operation, context)
            elif 'values' in operation:
                values = [await self._evaluate_value(v, context) for v in operation['values']]
                result = self._calculate(op_type, values)
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
            print(f"Error evaluating operation: {e}")
            context.pop_path()
            return 0

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
                    test_result = await self._evaluate_condition(condition['test'], context)
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

    async def _evaluate_value(self, value: Any, context: RuleContext) -> Any:
        """Evaluate a value which might be a number, operation, or reference"""
        if isinstance(value, (int, float)):
            return value
        elif isinstance(value, dict) and 'operation' in value:
            return await self._evaluate_operation(value, context)
        else:
            resolved = await context.resolve_value(value)
            return resolved if resolved is not None else 0
