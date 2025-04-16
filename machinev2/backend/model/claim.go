package model

import (
	"errors"

	"github.com/google/uuid"
)

var ErrClaimNotFound = errors.New("claim_not_found")

type Claim struct {
	ID           uuid.UUID
	Service      string
	Key          string
	CaseID       *uuid.UUID
	Law          string
	BSN          string
	Claimant     string
	EvidencePath *string
	NewValue     any
	OldValue     *any
	Reason       string
	Status       string
}

type ClaimSubmit struct {
	BSN          string
	CaseID       *uuid.UUID
	Claimant     string
	EvidencePath *string
	Key          string
	Law          string
	Service      string
	NewValue     any
	OldValue     *any
	Reason       string
	AutoApprove  *bool
}

type ClaimApprove struct {
	ID            uuid.UUID
	VerifiedBy    string
	VerifiedValue string
}

type ClaimReject struct {
	ID              uuid.UUID
	RejectedBy      string
	RejectionReason string
}
