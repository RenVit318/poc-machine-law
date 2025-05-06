package adapter

import (
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func ToCaseSubmit(record api.CaseSubmit) model.CaseSubmit {
	return model.CaseSubmit{
		BSN:                record.Bsn,
		Service:            record.Service,
		Law:                record.Law,
		ApprovedClaimsOnly: record.ApprovedClaimsOnly,
		ClaimedResult:      record.ClaimedResult,
		Parameters:         record.Parameters,
	}
}

func FromCase(case_ model.Case) api.Case {
	fmt.Printf("case_.AppealStatus: %v\n", case_.AppealStatus)
	return api.Case{
		Approved:           case_.Approved,
		ApprovedClaimsOnly: case_.ApprovedClaimsOnly,
		Bsn:                case_.BSN,
		ClaimedResult:      case_.ClaimedResult,
		Id:                 case_.ID,
		Law:                case_.Law,
		Parameters:         case_.Parameters,
		RulespecId:         case_.RuleSpecID,
		Service:            case_.Service,
		Status:             api.CaseStatus(case_.Status),
		VerifiedResult:     case_.VerifiedResult,
		AppealStatus:       case_.AppealStatus,
		ObjectionStatus:    FromCaseObjectionStatus(case_.ObjectionStatus),
	}
}

func FromCases(cases []model.Case) []api.Case {
	cs := make([]api.Case, 0, len(cases))

	for idx := range cases {
		cs = append(cs, FromCase(cases[idx]))
	}

	return cs
}

func FromCaseObjectionStatus(objection model.CaseObjectionStatus) *api.CaseObjectionStatus {
	return &api.CaseObjectionStatus{
		Admissable:        objection.Admissable,
		DecisionPeriod:    objection.DecisionPeriod,
		ExtensionPeriod:   objection.ExtensionPeriod,
		NotPossibleReason: objection.NotPossibleReason,
		ObjectionPeriod:   objection.ObjectionPeriod,
		Possible:          objection.Possible,
	}
}
