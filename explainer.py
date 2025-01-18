from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, auto
from typing import List, Dict, Any, Optional
from collections import defaultdict


class StepType(Enum):
    REQUIREMENT = auto()
    CALCULATION = auto()
    COMPARISON = auto()
    RESULT = auto()


class DataSource(Enum):
    USER_INPUT = "Opgegeven door gebruiker"
    SYSTEM_PARAM = "Systeemparameter"
    CALCULATED = "Berekende waarde"
    UNKNOWN = "Bron onbekend"


@dataclass
class DecisionStep:
    """Represents a single step in the decision process"""
    type: StepType
    description: str
    details: Dict[str, Any]
    importance: int = 1  # Higher number = more important in explanation
    data_source: DataSource = DataSource.UNKNOWN
    parent_step: Optional[str] = None  # For grouping related steps


@dataclass
class TemplateConfig:
    """Configuration for language templates"""
    requirement_met: str
    requirement_failed: str
    calculation: str
    comparison: str
    final_result: str
    money_format: str
    section_titles: Dict[str, str]
    operators: Dict[str, str]
    operations: Dict[str, str]


class PathExplainer:
    def __init__(self, rules_spec: Dict[str, Any], language: str = 'nl'):
        self.rules_spec = rules_spec
        self.language = language
        self.definitions = rules_spec.get('definitions', {})
        self.templates = self._load_templates()
        self.value_mappings = self._load_value_mappings()

    def _load_value_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load mappings for values and their sources"""
        return {
            'NATUURLIJKE_PERSOON': {
                'prefix': '',
                'mappings': {
                    'heeft_toeslagpartner': ('Er is een toeslagpartner', DataSource.USER_INPUT),
                    'leeftijd': ('De leeftijd', DataSource.USER_INPUT),
                    'toetsingsinkomen': ('Het toetsingsinkomen', DataSource.USER_INPUT),
                    'vermogen': ('Het vermogen', DataSource.USER_INPUT),
                    'verzekerde_zvw': ('De persoon is verzekerd voor zorg', DataSource.USER_INPUT),
                    'gedetineerd': ('De persoon is gedetineerd', DataSource.USER_INPUT),
                    'forensisch': ('De persoon is forensisch geplaatst', DataSource.USER_INPUT),
                }
            },
            'SYSTEM_PARAMS': {
                'prefix': 'Systeem: ',
                'mappings': {
                    'STANDAARDPREMIE_2024': ('Standaardpremie 2024', DataSource.SYSTEM_PARAM),
                    'DREMPELINKOMEN_ALLEENSTAANDE': ('Drempelinkomen alleenstaande', DataSource.SYSTEM_PARAM),
                    'PERCENTAGE_DREMPELINKOMEN_ALLEENSTAAND': (
                    'Percentage drempelinkomen alleenstaand', DataSource.SYSTEM_PARAM),
                    'AFBOUWPERCENTAGE_MINIMUM': ('Minimum afbouwpercentage', DataSource.SYSTEM_PARAM)
                }
            }
        }

    def _load_templates(self) -> TemplateConfig:
        """Load language-specific templates"""
        templates = {
            'nl': TemplateConfig(
                requirement_met='{description} ({value})',
                requirement_failed='{description} voldoet niet aan de voorwaarde ({value})',
                calculation='{description}: {result}',
                comparison='Vergelijking {value1} {operator} {value2}: {result}',
                final_result='De {object_name} is vastgesteld op {value}',
                money_format='€{:,.2f}',
                section_titles={
                    'requirements': 'Vereisten:',
                    'facts': 'Gegevens:',
                    'calculations': 'Berekening:',
                    'conclusion': 'Conclusie:',
                    'sources': 'Gegevensbronnen:'
                },
                operators={
                    'EQUALS': 'is',
                    'NOT_EQUALS': 'is niet',
                    'GREATER_THAN': 'is hoger dan',
                    'LESS_THAN': 'is lager dan',
                    'GREATER_OR_EQUAL': 'is minimaal',
                    'LESS_OR_EQUAL': 'is maximaal'
                },
                operations={
                    'ADD': 'Optelling van',
                    'SUBTRACT': 'Verschil tussen',
                    'MULTIPLY': 'Vermenigvuldiging van',
                    'DIVIDE': 'Deling van',
                    'MIN': 'Minimum van',
                    'MAX': 'Maximum van'
                }
            )
        }
        return templates[self.language]

    def format_money(self, value: Any) -> str:
        """Format a value as money"""
        if isinstance(value, (int, float)):
            euros = Decimal(value) / Decimal(100)
            return self.templates.money_format.format(euros).replace(',', '@').replace('.', ',').replace('@', '.')
        return str(value)

    def format_number(self, value: Any) -> str:
        """Format a numeric value"""
        if isinstance(value, float):
            return f"{value:.4f}".replace('.', ',')
        return str(value)

    def format_value(self, value: Any, as_money: bool = None) -> str:
        """Format a value based on its type and context"""
        if value is None:
            return "onbekend"
        if isinstance(value, bool):
            return 'wel' if value else 'niet'

        if as_money is not None:
            return self.format_money(value) if as_money else self.format_number(value)

        # Auto-detect money values (amounts over 100 are assumed to be cents)
        if isinstance(value, (int, float)):
            return self.format_money(value) if abs(value) > 100 else self.format_number(value)

        return str(value)

    def _get_readable_path(self, path: str) -> tuple[str, DataSource]:
        """Convert a path into a readable description and identify its source"""
        if not path.startswith('$'):
            return path, DataSource.UNKNOWN

        parts = path[1:].split('.')
        category = parts[0]

        if category in self.value_mappings:
            mapping_info = self.value_mappings[category]
            if len(parts) > 1 and parts[1] in mapping_info['mappings']:
                description, source = mapping_info['mappings'][parts[1]]
                return f"{mapping_info['prefix']}{description}", source

        return path[1:], DataSource.UNKNOWN

    def _extract_calculation_steps(self, node) -> List[DecisionStep]:
        """Extract detailed calculation steps from an operation node"""
        steps = []

        if node.type == 'operation' and 'operation_type' in node.details:
            op_type = node.details['operation_type']
            if 'evaluated_values' in node.details:
                values = [self.format_value(v, as_money=isinstance(v, (int, float)) and abs(v) > 100)
                          for v in node.details['evaluated_values']]

                # Create intermediate calculation steps
                if op_type == 'SUBTRACT':
                    steps.append(DecisionStep(
                        type=StepType.CALCULATION,
                        description=f"Basisbedrag",
                        details={'value': values[0]},
                        data_source=DataSource.SYSTEM_PARAM
                    ))
                    steps.append(DecisionStep(
                        type=StepType.CALCULATION,
                        description=f"Af: Eigen bijdrage",
                        details={'value': values[1]},
                        data_source=DataSource.CALCULATED
                    ))

                # Add the final calculation step
                steps.append(DecisionStep(
                    type=StepType.CALCULATION,
                    description=self.templates.operations.get(op_type, op_type),
                    details={
                        'values': values,
                        'result': self.format_value(node.result),
                        'operation': op_type
                    },
                    data_source=DataSource.CALCULATED
                ))

        return steps

    def _extract_steps_from_path(self, path_node) -> List[DecisionStep]:
        """Extract all decision steps from the path node"""
        steps = []
        requirements = []
        current_context = []

        def process_node(node, depth: int = 0):
            node_type = node.type
            details = node.details

            if node_type == 'test':
                if 'subject_path' in details:
                    description, source = self._get_readable_path(details['subject_path'])
                    step = DecisionStep(
                        type=StepType.COMPARISON,
                        description=description,
                        details={
                            'subject': details['subject_path'],
                            'operator': self.templates.operators.get(details['operator'], details['operator']),
                            'value': self.format_value(details['comparison_value']),
                            'actual': self.format_value(details['subject_value']),
                            'is_boolean': isinstance(details['subject_value'], bool)
                        },
                        data_source=source
                    )

                    if depth <= 1:  # Top-level requirements
                        requirements.append(step)
                    else:
                        steps.append(step)

            elif node_type == 'operation':
                calculation_steps = self._extract_calculation_steps(node)
                steps.extend(calculation_steps)

            elif node_type == 'action' and 'HOOGTE_TOESLAG' in node.name:
                steps.append(DecisionStep(
                    type=StepType.RESULT,
                    description=node.name,
                    details={
                        'object': 'zorgtoeslag',
                        'value': self.format_value(node.result, as_money=True)
                    },
                    importance=2,
                    data_source=DataSource.CALCULATED
                ))

            for child in node.children:
                process_node(child, depth + 1)

        process_node(path_node)
        return requirements + steps

    def explain_path(self, path_data: Dict[str, Any]) -> str:
        """Generate a human-readable explanation of the decision path"""
        steps = self._extract_steps_from_path(path_data['path'])

        # Group steps by type and source
        eligibility_checks = []  # Basic eligibility requirements
        income_checks = []  # Income and assets requirements
        calculation_steps = []  # Calculation process
        final_results = []  # Final outcomes

        # Track data sources for reference
        sources = {
            DataSource.USER_INPUT: [],
            DataSource.SYSTEM_PARAM: [],
            DataSource.CALCULATED: []
        }

        # Process steps into appropriate categories
        base_amount = None
        eigen_bijdrage = None

        for step in steps:
            # Track data sources
            if step.data_source in sources:
                source_desc = f"{step.description}"
                if 'actual' in step.details:
                    source_desc += f" ({step.details['actual']})"
                elif 'value' in step.details:
                    source_desc += f" ({step.details['value']})"
                sources[step.data_source].append(source_desc)

            if step.type == StepType.RESULT:
                final_results.append(
                    self.templates.final_result.format(
                        object_name=step.details['object'],
                        value=step.details['value']
                    )
                )

            elif step.type == StepType.COMPARISON:
                if step.details.get('is_boolean', False):
                    desc = step.description
                    is_true = step.details.get('actual', True)

                    # Handle boolean description
                    if not is_true:
                        if desc.startswith('Er is een'):
                            desc = desc.replace('Er is een', 'Er is geen')
                        elif 'is' in desc:
                            parts = desc.split(' is ')
                            desc = f"{parts[0]} is niet {' '.join(parts[1:])}"
                        else:
                            desc += ' niet'

                    # Categorize basic eligibility vs income requirements
                    if any(key in desc.lower() for key in ['inkomen', 'vermogen', 'toeslagpartner']):
                        income_checks.append(f"- {desc}")
                    else:
                        eligibility_checks.append(f"- {desc}")

                else:
                    # Handle numeric comparisons
                    if 'leeftijd' in step.description.lower():
                        eligibility_checks.append(
                            f"- {step.description}: {step.details['actual']} jaar "
                            f"(minimumleeftijd: {step.details['value']})"
                        )
                    else:
                        income_checks.append(
                            f"- {step.description}: {step.details['actual']} "
                            f"(grens: {step.details['value']})"
                        )

            elif step.type == StepType.CALCULATION:
                details = step.details
                desc = step.description

                # Track important calculation values
                if desc == "Basisbedrag":
                    base_amount = details['value']
                elif desc == "Af: Eigen bijdrage":
                    eigen_bijdrage = details['value']

                # Format calculation step
                calc_text = f"└─ {desc}"
                if 'values' in details:
                    calc_text += f": {' en '.join(details['values'])}"
                if 'result' in details:
                    calc_text += f" = {details['result']}"

                calculation_steps.append(calc_text)

        # Build the explanation
        explanation = []

        # Start with conclusion
        if final_results:
            explanation.append(self.templates.section_titles['conclusion'])
            explanation.extend(final_results)
            explanation.append("")

        # Add requirements section
        if eligibility_checks:
            explanation.append("Basis vereisten:")
            explanation.extend(eligibility_checks)
            explanation.append("")

        if income_checks:
            explanation.append("Inkomens- en vermogenstoets:")
            explanation.extend(income_checks)
            explanation.append("")

        # Add calculation section with clear structure
        if calculation_steps:
            explanation.append("Berekening zorgtoeslag:")
            if base_amount:
                explanation.append(f"1. Standaard zorgtoeslag: {base_amount}")
            if eigen_bijdrage:
                explanation.append(f"2. Eigen bijdrage berekening:")
            explanation.extend(calculation_steps)
            explanation.append("")

        # Add data sources section
        explanation.append("Bronnen van gegevens:")

        if sources[DataSource.USER_INPUT]:
            explanation.append("  Opgegeven door gebruiker:")
            for item in sorted(set(sources[DataSource.USER_INPUT])):
                explanation.append(f"  └─ {item}")

        if sources[DataSource.SYSTEM_PARAM]:
            if sources[DataSource.USER_INPUT]:  # Add spacing if previous section exists
                explanation.append("")
            explanation.append("  Systeemparameters:")
            for item in sorted(set(sources[DataSource.SYSTEM_PARAM])):
                explanation.append(f"  └─ {item}")

        return "\n".join(explanation)
