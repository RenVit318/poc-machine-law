from typing import Dict, Any

import yaml

from engine import AbstractServiceProvider
from services.base import BaseService, ServiceConfig, ServiceError
from services.belastingdienst import BelastingdienstService
from services.brp import BRPService
from services.dji import DJIService
from services.duo import DUOService
from services.rvz import RVZService
from services.uwv import UWVService


class ServiceProvider(AbstractServiceProvider):
    def __init__(self, config_path: str):
        self.services: Dict[str, BaseService] = {}
        self.service_classes = [
            BRPService,
            RVZService,
            DJIService,
            UWVService,
            BelastingdienstService,
            DUOService,
        ]
        self._load_config(config_path)

    def _load_config(self, config_path: str):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        for service_config in config['services']:
            name = service_config['name']
            for service_class in self.service_classes:
                if service_class.name != name:
                    continue
                config_obj = ServiceConfig(
                    name=name,
                    endpoint=f"{service_config.get('endpoint', '')}",
                    grant_hash=service_config.get('grant_hash', ''),
                    rvva_id=service_config.get('rvva_id', '')
                )
                self.services[name] = service_class(config_obj)

    async def get_value(self, service: str, method: str, context: Dict[str, Any]) -> Any:
        print(f"Actually fetching {service}.{method}")

        if service in self.services:
            self.services[service].traceparent = context.get('traceparent')
            self.services[service].bsn = context.get('bsn')
            value = await self.services[service].get_method_value(method, context)
            print(f" - Fetched: {value}")
            return value
        return None


# Usage example:
if __name__ == "__main__":
    provider = ServiceProvider("config.yaml")
    try:
        result = provider.get_value("BRP", "age", {"bsn": "123456789"})
        print(f"Result: {result}")
    except ServiceError as e:
        print(f"Service error occurred: {e}")
    except ValueError as e:
        print(f"Validation error: {e}")
