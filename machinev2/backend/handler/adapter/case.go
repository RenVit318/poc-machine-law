package adapter

import (
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
		ObjectionStatus:    case_.ObjectionStatus,
	}
}

func FromCases(cases []model.Case) []api.Case {
	cs := make([]api.Case, 0, len(cases))

	for idx := range cases {
		cs = append(cs, FromCase(cases[idx]))
	}

	return cs
}
