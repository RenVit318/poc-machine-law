from dataclasses import dataclass
from typing import Dict, Any, Optional

from engine import RulesEngine
from services.services import ServiceProvider
from utils import RuleResolver


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

    def __init__(self, service_name: str, provider_config: str = "services.yaml"):
        """
        Initialize service for specific business rules

        Args:
            service_name: Name of the service (e.g. "TOESLAGEN")
            provider_config: Path to service provider configuration
        """
        self.service_name = service_name
        self.provider = ServiceProvider(provider_config)
        self.resolver = RuleResolver()
        self._engines: Dict[str, Dict[str, RulesEngine]] = {}

    def _get_engine(self, law: str, reference_date: str) -> RulesEngine:
        """Get or create RulesEngine instance for given law and date"""
        if law not in self._engines:
            self._engines[law] = {}

        if reference_date not in self._engines[law]:
            spec = self.resolver.get_rule_spec(law, reference_date)
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
                service_provider=self.provider
            )

        return self._engines[law][reference_date]

    async def evaluate(
            self,
            law: str,
            reference_date: str,
            service_context: Dict[str, Any],
            overwrite_input: Optional[Dict[str, Any]] = None
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
            overwrite_input=overwrite_input
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


# Example usage:
async def main():
    # Initialize service
    toeslagen = RuleService("TOESLAGEN")

    # Get rule info
    rule_info = toeslagen.get_rule_info("zorgtoeslagwet", "2025-01-01")
    print(f"Using rule: {rule_info}")

    # Evaluate rules
    result = await toeslagen.evaluate(
        law="zorgtoeslagwet",
        reference_date="2025-01-01",
        service_context={'bsn': '999993653'},
        overwrite_input={"@BRP.age": 19}
    )

    # Access results
    print(f"Requirements met: {result.requirements_met}")
    print(f"Outputs: {result.output}")
    print(f"Inputs used: {result.input}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
