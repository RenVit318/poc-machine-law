from enum import Enum
from typing import Dict, Any
from typing import List
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, constr

from .base import BaseService, ServiceConfig


# Generated models
class Operator(str, Enum):
    equal = "equal"
    greater_than = "greaterThan"
    less_than = "lessThan"
    greater_than_or_equal = "greaterThanOrEqual"
    less_than_or_equal = "lessThanOrEqual"


class NetWorth(BaseModel):
    id: UUID
    bsn: constr(pattern=r"^[0-9]{9}$")
    netWorth: int = Field(..., description="net worth in cents")


class NetWorthUpdate(BaseModel):
    net_worth: int = Field(..., description="net worth in cents")


class NetWorthCalculator(BaseModel):
    result: bool


class BelastingdienstClient:
    def __init__(self, base_url: str, headers: dict):
        self.base_url = base_url.rstrip('/')
        self.headers = headers

    async def get_net_worth(self, bsn: str) -> NetWorth:
        """Get net worth for a specific BSN"""
        url = f"{self.base_url}/v0/personen/{bsn}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return NetWorth.parse_obj(response.json())

    async def update_net_worth(self, bsn: str, net_worth: NetWorthUpdate) -> None:
        """Update net worth for a specific BSN"""
        url = f"{self.base_url}/personen/{bsn}"
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url,
                headers=self.headers,
                json={"data": net_worth.dict()}
            )
            response.raise_for_status()

    async def calculate_net_worth(
            self,
            amount: int,
            operator: Operator,
            bsns: List[str]
    ) -> NetWorthCalculator:
        """Calculate net worth based on criteria"""
        url = f"{self.base_url}/netWorth"
        params = {
            "amount": amount,
            "operator": operator.value,
            "bsns": ",".join(bsns)
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return NetWorthCalculator.parse_obj(response.json())


# Usage example with the ServiceProvider
class BelastingdienstService(BaseService):
    name = "BELASTINGDIENST"

    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.client = BelastingdienstClient(
            base_url=config.endpoint,
            headers=self._get_headers()
        )

    async def get_method_value(self, method: str, context: Dict[str, Any]) -> int | None:
        self._validate_context(context)
        bsn = context['bsn']

        if method == 'net_worth':
            result = await self.client.get_net_worth(bsn)
            return result.netWorth

        elif method == 'combined_net_worth':
            result = await self.client.get_net_worth(bsn)
            result_partner = await self.client.get_net_worth(context.get('partner_bsn', ''))
            return result.netWorth + result_partner.netWorth

        return None
