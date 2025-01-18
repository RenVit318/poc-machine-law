from typing import Dict, Any

from services.base import BaseService


class DJIService(BaseService):
    name = "DJI"

    async def get_method_value(self, method: str, context: Dict[str, Any]) -> Any:
        self._validate_context(context)
        # Mock data since no endpoint is configured
        method_mapping = {
            'is_incarcerated': False,
            'is_forensic': False
        }
        return method_mapping.get(method)
