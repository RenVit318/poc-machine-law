from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID


@dataclass
class CaseStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    DECIDED = "DECIDED"
    IN_REVIEW = "IN_REVIEW"
    OBJECTED = "OBJECTED"


@dataclass
class Case:
    """Case"""

    id: UUID
    bsn: str
    service: str
    law: str
    rulespec_uuid: UUID
    approved_claims_only: bool
    status: CaseStatus
    parameters: dict[str, Any] = field(default_factory=dict)
    claimed_result: dict[str, Any] = field(default_factory=dict)
    verified_result: dict[str, Any] = field(default_factory=dict)
    objection_status: dict[str, Any] = field(default_factory=dict)
    appeal_status: dict[str, Any] = field(default_factory=dict)
    approved: bool | None = None

    def can_object(self) -> bool:  # TODO: FIX
        return False

    def can_appeal(self) -> bool:
        return False
