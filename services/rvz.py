from typing import Dict, Any
from uuid import UUID

import httpx
from pydantic import BaseModel, constr

from services.base import BaseService, ServiceConfig


# Generated models
class HealthInsurance(BaseModel):
    id: UUID
    bsn: constr(pattern=r"^[0-9]{9}$")
    hasInsurance: bool


class RVZService(BaseService):
    name = "RVZ"

    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.config = config

    async def get_method_value(self, method: str, context: Dict[str, Any]) -> Any:
        self._validate_context(context)

        if method == 'has_insurance':
            result = await self._get_health_insurance(context['bsn'])
            return result.hasInsurance

        return None

    async def _get_health_insurance(self, bsn: str) -> HealthInsurance:
        """Get health insurance status for a specific BSN"""
        url = f"{self.config.endpoint}/v0/personen/{bsn}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()
            return HealthInsurance.parse_obj(response.json())
