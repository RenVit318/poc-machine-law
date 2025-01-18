from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

import requests
from requests import RequestException


@dataclass
class ServiceConfig:
    name: str
    endpoint: str
    grant_hash: str
    rvva_id: str


class ServiceError(Exception):
    pass


class BaseService(ABC):
    name: str = None  # Will be overridden by each service class
    traceparent: str = None
    bsn: str = None

    def __init__(self, config: ServiceConfig):
        if not self.name:
            raise ValueError(f"Service class {self.__class__.__name__} must define a name")
        self.config = config

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'Authorization': "Basic ZGlnaWxhYjpwYWR2ZmllbGRsYWI=",
            'X-Dpl-Rva-Activity-Id': self.config.rvva_id,
            'Fsc-Grant-Hash': self.config.grant_hash,
        }
        if self.traceparent:
            headers['traceparent'] = self.traceparent

        if self.bsn:
            headers['X-Dpl-Core-User'] = self.bsn

        return headers

    def _validate_context(self, context: Dict[str, Any]) -> None:
        if 'bsn' not in context:
            raise ValueError("BSN is required in context")

    def _make_request(self, method: str, context: Dict[str, Any]) -> Optional[Any]:
        if not self.config.endpoint:
            return None

        try:
            response = requests.get(
                f"{self.config.endpoint}/{self.name.lower()}/{method}",
                headers=self._get_headers(),
                params={'bsn': context['bsn']}
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise ServiceError(f"Error calling {self.name}.{method}: {str(e)}")

    @abstractmethod
    def get_method_value(self, method: str, context: Dict[str, Any]) -> Any:
        pass
