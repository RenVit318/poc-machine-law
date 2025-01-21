import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Any, Optional

from engine import RulesEngine, AbstractServiceProvider
from logging_config import IndentLogger
from utils import RuleResolver

logger = IndentLogger(logging.getLogger('service'))


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""
    output: Dict[str, Any]
    requirements_met: bool
    input: Dict[str, Any]

    @classmethod
    def from_engine_result(cls, result: Dict[str, Any]) -> 'RuleResult':
        """Create RuleResult from engine evaluation result"""
        return cls(
            output={
                name: data.get('value')
                for name, data in result.get('output', {}).items()
            },
            requirements_met=result.get('requirements_met', False),
            input=result.get('input', {}),
        )


class RuleService:
    """Interface for executing business rules for a specific service"""

    def __init__(self, service_name: str, services):
        """
        Initialize service for specific business rules

        Args:
            service_name: Name of the service (e.g. "TOESLAGEN")
            services: parent services
        """
        self.service_name = service_name
        self.services = services
        self.resolver = RuleResolver()
        self._engines: Dict[str, Dict[str, RulesEngine]] = {}
        self.source_values = defaultdict(dict)

    def _get_engine(self, law: str, reference_date: str) -> RulesEngine:
        """Get or create RulesEngine instance for given law and date"""
        if law not in self._engines:
            self._engines[law] = {}

        if reference_date not in self._engines[law]:
            spec = self.resolver.get_rule_spec(law, reference_date, service=self.service_name)
            if not spec:
                raise ValueError(
                    f"No rules found for law '{law}' at date '{reference_date}'"
                )
            if spec.get('service') != self.service_name:
                raise ValueError(
                    f"Rule spec service '{spec.get('service')}' does not match "
                    f"service '{self.service_name}'"
                )
            self._engines[law][reference_date] = RulesEngine(
                spec=spec,
                service_provider=self.services
            )

        return self._engines[law][reference_date]

    async def evaluate(
            self,
            law: str,
            reference_date: str,
            service_context: Dict[str, Any],
            overwrite_input: Optional[Dict[str, Any]] = None,
            requested_output: str = None
    ) -> RuleResult:
        """
        Evaluate rules for given law and reference date

        Args:
            law: Name of the law (e.g. "zorgtoeslagwet")
            reference_date: Reference date for rule version (YYYY-MM-DD)
            service_context: Context data for service provider
            overwrite_input: Optional overrides for input values

        Returns:
            RuleResult containing outputs and metadata
        """
        engine = self._get_engine(law, reference_date)
        result = await engine.evaluate(
            service_context=service_context,
            overwrite_input=overwrite_input,
            sources=self.source_values,
            calculation_date=reference_date,
            requested_output=requested_output,
        )
        return RuleResult.from_engine_result(result)

    def get_rule_info(self, law: str, reference_date: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about the rule that would be applied for given law and date

        Returns dict with uuid, name, valid_from if rule is found
        """
        try:
            rule = self.resolver.find_rule(law, reference_date)
            if rule:
                return {
                    'uuid': rule.uuid,
                    'name': rule.name,
                    'valid_from': rule.valid_from.strftime('%Y-%m-%d')
                }
        except ValueError:
            return None
        return None

    def set_source_value(self, table: str, field: str, value: Any):
        """Set a source value override"""
        self.source_values[table][field] = value


class Services(AbstractServiceProvider):
    def __init__(self, reference_date: str):
        self.resolver = RuleResolver()
        self.service_laws = self.resolver.get_service_laws()
        self.services = {service: RuleService(service, self) for service in self.service_laws}
        self.root_reference_date = reference_date

    def set_source_value(self, service: str, table: str, field: str, value: Any):
        """Set a source value override"""
        self.services[service].set_source_value(table, field, value)

    async def evaluate(
            self,
            service: str,
            law: str,
            reference_date: str,
            service_context: Dict[str, Any],
            overwrite_input: Optional[Dict[str, Any]] = None,
            requested_output: str = None
    ) -> RuleResult:
        with logger.indent_block(f"{service}: {law} ({reference_date} {service_context} {requested_output})",
                                 double_line=True):
            return await self.services[service].evaluate(
                law=law,
                reference_date=reference_date,
                service_context=service_context,
                overwrite_input=overwrite_input,
                requested_output=requested_output,
            )

    async def get_value(
            self,
            service: str,
            law: str,
            field: str,
            temporal: Dict[str, Any],
            context: Dict[str, Any],
            overwrite_input: Dict[str, Any]) -> Any:
        # reference_date = None
        # if temporal['reference_date'] == "calculation_date":
        reference_date = self.root_reference_date
        result = await self.evaluate(service, law, reference_date, context, overwrite_input, requested_output=field)
        return result.output.get(field)
