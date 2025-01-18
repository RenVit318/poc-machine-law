from datetime import datetime
from typing import Dict, Any, Optional

import httpx

from services.base import BaseService


class DUOService(BaseService):
    name = "DUO"

    async def get_method_value(self, method: str, context: Dict[str, Any]) -> Any:
        self._validate_context(context)

        try:
            if method == 'study_grant':
                # Get income for main BSN
                return await self._get_study_grant(context['bsn'], context.get('datetime'))
            elif method == 'partner_study_grant':
                # Get income for partner BSN if available
                if 'partner_bsn' not in context:
                    return None
                return await self._get_study_grant(context['partner_bsn'], context.get('datetime'))
            return None

        except httpx.RequestError as e:
            print(f"Error calling DUO service: {e}")
            return None

    async def _get_study_grant(self, bsn: str, datetime_param: Optional[datetime] = None) -> Optional[float]:
        params = {}
        if datetime_param:
            # Format datetime as ISO 8601 string as required by the API
            params['validAt'] = datetime_param.isoformat()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.config.endpoint}/v0/personen/{bsn}",
                    params=params,
                    headers=self._get_headers()
                )

                if response.status_code == 200:
                    data = response.json()
                    # Only return amount if student has an active grant
                    if data.get('hasStudentGrant'):
                        return data.get('amount')
                    return None
                elif response.status_code == 400:
                    print(f"Bad request error for BSN {bsn}: {response.json().get('errors', [])}")
                    return None
                elif response.status_code == 500:
                    print(f"Internal server error for BSN {bsn}: {response.json().get('errors', [])}")
                    return None
                else:
                    print(f"Unexpected status code {response.status_code} for BSN {bsn}")
                    return None

            except httpx.RequestError as e:
                print(f"Error calling DUO service for BSN {bsn}: {e}")
                return None
            except Exception as e:
                print(f"Unexpected error processing DUO response for BSN {bsn}: {e}")
                return None
