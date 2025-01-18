from typing import Dict, Any

import httpx
from pydantic import BaseModel

from services.base import BaseService


class IncomeIncome(BaseModel):
    monthly: int
    yearly: int


class Income(BaseModel):
    id: str
    bsn: str
    income: IncomeIncome


class UWVService(BaseService):
    name = "UWV"

    async def get_method_value(self, method: str, context: Dict[str, Any]) -> int | None:
        self._validate_context(context)

        try:
            if method == 'income':
                # Get income for main BSN
                return await self._get_income(context['bsn'])
            elif method == 'partner_income':
                # Get income for partner BSN if available
                if 'partner_bsn' not in context:
                    return None
                return await self._get_income(context['partner_bsn'])
            return None

        except httpx.RequestError as e:
            print(f"Error calling UWV service: {e}")
            return None

    async def _get_income(self, bsn: str) -> int:
        """Get monthly income in cents for a BSN"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.config.endpoint}/v0/personen/{bsn}",
                headers=self._get_headers()
            )
            response.raise_for_status()

            # Parse response into model
            income_data = Income.model_validate(response.json())

            # Return monthly income
            return income_data.income.yearly
