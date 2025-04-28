package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromClaim(claim model.Claim) api.Claim {
	return api.Claim{
		Bsn:          claim.BSN,
		CaseId:       claim.CaseID,
		Claimant:     claim.Claimant,
		EvidencePath: claim.EvidencePath,
		Id:           claim.ID,
		Key:          claim.Key,
		Law:          claim.Law,
		NewValue:     claim.NewValue,
		OldValue:     claim.OldValue,
		Reason:       claim.Reason,
		Service:      claim.Service,
		Status:       api.ClaimStatus(claim.Status),
	}
}

func FromClaims(claims []model.Claim) []api.Claim {
	cs := make([]api.Claim, 0, len(claims))

	for idx := range claims {
		cs = append(cs, FromClaim(claims[idx]))
	}

	return cs
}
