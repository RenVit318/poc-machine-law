from typing import Any
from uuid import UUID

import httpx

from ..claim_manager_interface import ClaimManagerInterface
from ..models import Claim
from .machine_client.law_as_code_client import Client
from .machine_client.law_as_code_client.api.claim import (
    claim_approve,
    claim_reject,
    claim_submit,
    get_claims_bsn,
    get_claims_bsn_service_law,
)
from .machine_client.law_as_code_client.models import (
    ClaimApprove,
    ClaimApproveBody,
    ClaimReject,
    ClaimRejectBody,
    ClaimSubmit,
    ClaimSubmitBody,
)


class ClaimManager(ClaimManagerInterface):
    """
    Implementation of ClaimManagerInterface that uses the embedded Python machine.service library.
    """

    def __init__(self, base_url: str = "http://localhost:8081/v0"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def get_claims_by_bsn(self, bsn: str, approved: bool = False, include_rejected: bool = False) -> list[Claim]:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = get_claims_bsn.sync_detailed(
                client=client, bsn=bsn, approved=approved, include_rejected=include_rejected
            )

            return to_claims(response.parsed.data)

    async def get_claim_by_bsn_service_law(
        self, bsn: str, service: str, law: str, approved: bool = False, include_rejected: bool = False
    ) -> dict[UUID:Claim]:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            response = get_claims_bsn_service_law.sync_detailed(
                client=client, bsn=bsn, service=service, law=law, approved=approved, include_rejected=include_rejected
            )

            return to_dict_claims(response.parsed.data.additional_properties)

    async def submit_claim(
        self,
        service: str,
        key: str,
        new_value: Any,
        reason: str,
        claimant: str,
        law: str,
        bsn: str,
        case_id: UUID | None = None,
        old_value: Any | None = None,
        evidence_path: str | None = None,
        auto_approve: bool = False,  # Add this parameter
    ) -> UUID:
        """
        Submit a new claim. Can be linked to an existing case or standalone.
        If auto_approve is True, the claim will be automatically approved.

        Args:
            service:

        Returns:
            A ClaimID
        """

        if case_id == "":
            case_id = None

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = ClaimSubmit(
            service=service,
            key=key,
            new_value=new_value,
            reason=reason,
            claimant=claimant,
            law=law,
            bsn=bsn,
            case_id=case_id,
            old_value=old_value,
            evidence_path=evidence_path,
            auto_approve=auto_approve,
        )
        body = ClaimSubmitBody(data=data)

        with client as client:
            response = claim_submit.sync_detailed(client=client, body=body)
            content = response.parsed

            return content.data

    async def reject_claim(self, claim_id: UUID, rejected_by: str, rejection_reason: str) -> None:
        """
        Reject a claim with reason

        Args:
            claim_id: Identifier of the claim
            rejected_by: User that rejected the claim
            rejection_reason: Reason of the rejection

        Returns:
            None
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = ClaimReject(rejected_by=rejected_by, rejection_reason=rejection_reason)
        body = ClaimRejectBody(data=data)

        with client as client:
            claim_reject.sync_detailed(client=client, claim_id=claim_id, body=body)

    async def approve_claim(self, claim_id: UUID, verified_by: str, verified_value: str) -> None:
        """
        Approve a claim with verified value

        Args:
            claim_id: Identifier of the claim
            verified_by: User that verified the claim
            verified_value: Verified value

        Returns:
            None
        """

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = ClaimApprove(verified_by=verified_by, verified_value=verified_value)
        body = ClaimApproveBody(data=data)

        with client as client:
            claim_approve.sync_detailed(client=client, claim_id=claim_id, body=body)


def to_claim(claim) -> Claim:
    return Claim(
        id=claim.id,
        service=claim.service,
        key=claim.key,
        new_value=claim.new_value,
        reason=claim.reason,
        claimant=claim.claimant,
        law=claim.law,
        bsn=claim.bsn,
        status=claim.status,
        case_id=claim.case_id,
        old_value=claim.old_value,
        evidence_path=claim.evidence_path,
    )


def to_claims(claims: list[Any]) -> list[Claim]:
    return [to_claim(item) for item in claims]


def to_dict_claims(claims: dict[UUID:Any]) -> dict[UUID:Claim]:
    return {k: to_claim(item) for k, item in claims.items()}
