package service

import (
	"context"
	"fmt"

	"github.com/looplab/eventhorizon/uuid"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/casemanager"
)

func (service *Service) CaseGetBasedOnBSNServiceLaw(ctx context.Context, bsn, svc, law string) (model.Case, error) {
	record, err := service.service.CaseManager.GetCase(ctx, bsn, svc, law)
	if err != nil {
		return model.Case{}, fmt.Errorf("get case by bsn: %w", err)
	}

	if record == nil {
		return model.Case{}, model.ErrCaseNotFound
	}

	return ToCase(record), nil
}

func (service *Service) CaseListBasedOnServiceLaw(ctx context.Context, svc, law string) ([]model.Case, error) {
	records, err := service.service.CaseManager.GetCasesByLaw(ctx, svc, law)
	if err != nil {
		return nil, fmt.Errorf("get case by bsn: %w", err)
	}

	if records == nil {
		return []model.Case{}, nil
	}

	return ToCases(records), nil
}

// CaseGet implements Servicer.
func (service *Service) CaseGet(ctx context.Context, caseID uuid.UUID) (model.Case, error) {
	record, err := service.service.CaseManager.GetCaseByID(ctx, caseID)
	if err != nil {
		return model.Case{}, fmt.Errorf("get case by id: %w", err)
	}

	return ToCase(record), nil
}

// CaseSubmit implements Servicer.
func (service *Service) CaseSubmit(ctx context.Context, case_ model.CaseSubmit) (uuid.UUID, error) {
	caseID, err := service.service.CaseManager.SubmitCase(
		ctx,
		case_.BSN,
		case_.Service,
		case_.Law,
		case_.Parameters,
		case_.ClaimedResult,
		case_.ApprovedClaimsOnly,
	)

	if err != nil {
		return uuid.Nil, fmt.Errorf("submit case: %w", err)
	}

	return caseID, nil
}

func (service *Service) CaseReview(ctx context.Context, case_ model.CaseReview) (uuid.UUID, error) {
	err := service.service.CaseManager.CompleteManualReview(ctx, case_.CaseID, case_.VerifierID, case_.Approved, case_.Reason, nil)
	if err != nil {
		return uuid.Nil, fmt.Errorf("complete manual review: %w", err)
	}

	return case_.CaseID, nil
}

func ToCase(case_ *casemanager.Case) model.Case {
	return model.Case{
		ID:                 case_.ID,
		Service:            case_.Service,
		Law:                case_.Law,
		BSN:                case_.BSN,
		Status:             string(case_.Status),
		Approved:           case_.Approved,
		ApprovedClaimsOnly: case_.ApprovedClaimsOnly,
		ClaimedResult:      case_.ClaimedResult,
		VerifiedResult:     case_.VerifiedResult,
		Parameters:         case_.Parameters,
		RuleSpecID:         case_.RulespecID,
		AppealStatus:       &case_.AppealStatus,
		ObjectionStatus:    &case_.ObjectionStatus,
	}
}

func ToCases(cases []*casemanager.Case) []model.Case {
	cs := make([]model.Case, 0, len(cases))

	for idx := range cases {
		cs = append(cs, ToCase(cases[idx]))
	}

	return cs
}
