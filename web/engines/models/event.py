from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


@dataclass
class EventType(str, Enum):
    SUBMITTED = "SUBMITTED"
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    OBJECTED = "OBJECTED"


@dataclass
class EventData:
    approved: bool
    claimed_result: dict[str, Any]
    reason: str
    verified_result: dict[str, Any]


@dataclass
class Event:
    """Event"""

    event_type: EventType
    timestamp: datetime
    data: EventData
