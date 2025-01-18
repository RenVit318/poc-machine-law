from typing import Dict, Any
from typing import List

import httpx
from pydantic import BaseModel

from services.base import BaseService


class PersonenQuery(BaseModel):
    type: str = "RaadpleegMetBurgerservicenummer"
    burgerservicenummer: List[str]
    fields: List[str]


class BRPService(BaseService):
    name = "BRP"

    async def get_method_value(self, method: str, context: Dict[str, Any]) -> Any:
        self._validate_context(context)

        # Map our simple methods to the actual BRP fields we need
        field_mapping = {
            'age': ['leeftijd'],
            'has_partner': ['partners']
        }

        if method not in field_mapping:
            return None

        # Construct the query
        query = PersonenQuery(
            burgerservicenummer=[context['bsn']],
            fields=field_mapping[method]
        )

        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.config.endpoint}/haalcentraal/api/brp/personen"
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=query.model_dump()
                )
                response.raise_for_status()
                data = response.json()

                # Extract and transform the requested data
                if 'personen' in data and len(data['personen']) > 0:
                    person = data['personen'][0]

                    if method == 'age':
                        return person.get('leeftijd')
                    elif method == 'has_partner':
                        # Check if there are any current partners
                        partners = person.get('partners', [])
                        for partner in partners:
                            if not partner.get('burgerservicenummer'):
                                continue
                            # Check if this is a current partner (no ontbindingHuwelijkPartnerschap)
                            if not partner.get('ontbindingHuwelijkPartnerschap'):
                                context['partner_bsn'] = partner.get('burgerservicenummer')
                                return True
                        return False

                return None

        except httpx.RequestError as e:
            print(f"Error calling BRP service: {e}")
            return None
