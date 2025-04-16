from collections.abc import Mapping
from typing import Any, TypeVar, Union
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.case_status import CaseStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Case")


@_attrs_define
class Case:
    """Case

    Attributes:
        id (UUID): Identifier of a case
        bsn (str): Burgerservicenummer of a Dutch citizen Example: 111222333.
        service (str): Specify the service that needs to be executed
        law (str): Specify the law that needs to be executed
        parameters (Any):
        claimed_result (Any):
        verified_result (Any):
        approved_claims_only (bool):
        rulespec_id (UUID): Identifier of the rulespec
        status (CaseStatus):
        approved (Union[Unset, bool]):
        objection_status (Union[Unset, Any]):
        appeal_status (Union[Unset, Any]):
    """

    id: UUID
    bsn: str
    service: str
    law: str
    parameters: Any
    claimed_result: Any
    verified_result: Any
    approved_claims_only: bool
    rulespec_id: UUID
    status: CaseStatus
    approved: Union[Unset, bool] = UNSET
    objection_status: Union[Unset, Any] = UNSET
    appeal_status: Union[Unset, Any] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        bsn = self.bsn

        service = self.service

        law = self.law

        parameters = self.parameters

        claimed_result = self.claimed_result

        verified_result = self.verified_result

        approved_claims_only = self.approved_claims_only

        rulespec_id = str(self.rulespec_id)

        status = self.status.value

        approved = self.approved

        objection_status = self.objection_status

        appeal_status = self.appeal_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "bsn": bsn,
                "service": service,
                "law": law,
                "parameters": parameters,
                "claimedResult": claimed_result,
                "verifiedResult": verified_result,
                "approvedClaimsOnly": approved_claims_only,
                "rulespecId": rulespec_id,
                "status": status,
            }
        )
        if approved is not UNSET:
            field_dict["approved"] = approved
        if objection_status is not UNSET:
            field_dict["objectionStatus"] = objection_status
        if appeal_status is not UNSET:
            field_dict["appealStatus"] = appeal_status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        bsn = d.pop("bsn")

        service = d.pop("service")

        law = d.pop("law")

        parameters = d.pop("parameters")

        claimed_result = d.pop("claimedResult")

        verified_result = d.pop("verifiedResult")

        approved_claims_only = d.pop("approvedClaimsOnly")

        rulespec_id = UUID(d.pop("rulespecId"))

        status = CaseStatus(d.pop("status"))

        approved = d.pop("approved", UNSET)

        objection_status = d.pop("objectionStatus", UNSET)

        appeal_status = d.pop("appealStatus", UNSET)

        case = cls(
            id=id,
            bsn=bsn,
            service=service,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            verified_result=verified_result,
            approved_claims_only=approved_claims_only,
            rulespec_id=rulespec_id,
            status=status,
            approved=approved,
            objection_status=objection_status,
            appeal_status=appeal_status,
        )

        case.additional_properties = d
        return case

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
