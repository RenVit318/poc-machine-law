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
class Event:
    """Event"""

    event_type: EventType
    timestamp: datetime
    data: dict[str, Any]
