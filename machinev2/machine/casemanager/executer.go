package casemanager

import (
	"context"

	eh "github.com/looplab/eventhorizon"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
)

var _ eh.EventHandler = &Executor{}

// Executor is a simple event handler for logging all events.
type Executor struct {
	logger logging.Logger
	cb     Callback
}

func NewExecutor(logger logging.Logger, cb Callback) *Executor {
	return &Executor{
		logger: logger,
		cb:     cb,
	}
}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (l *Executor) HandlerType() eh.EventHandlerType {
	return "executor"
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (l *Executor) HandleEvent(ctx context.Context, event eh.Event) error {
	switch data := event.Data().(type) {
	case *CaseSubmitted:
		l.cb(event.AggregateID(), "Submitted", map[string]any{
			"bsn":                  data.BSN,
			"service_type":         data.ServiceType,
			"law":                  data.Law,
			"parameters":           data.Parameters,
			"claimed_result":       data.ClaimedResult,
			"verified_result":      data.VerifiedResult,
			"rulespec_uuid":        data.RulespecUUID,
			"approved_claims_only": data.ApprovedClaimsOnly,
		})
	case *CaseDecided:
		// Record the event
		l.cb(event.AggregateID(), "Decided", map[string]any{
			"verified_result": data.VerifiedResult,
			"reason":          data.Reason,
			"verifier_id":     data.VerifierID,
			"approved":        data.Approved,
		})
	case *CaseObjected:
		l.cb(event.AggregateID(), "Objected", map[string]any{
			"reason": data.Reason,
		})
	case *ObjectionStatusDetermined:
		// Record the event
		eventData := make(map[string]any)
		if data.Possible != nil {
			eventData["possible"] = *data.Possible
		}
		if data.NotPossibleReason != nil {
			eventData["not_possible_reason"] = *data.NotPossibleReason
		}
		if data.ObjectionPeriod != nil {
			eventData["objection_period"] = *data.ObjectionPeriod
		}
		if data.DecisionPeriod != nil {
			eventData["decision_period"] = *data.DecisionPeriod
		}
		if data.ExtensionPeriod != nil {
			eventData["extension_period"] = *data.ExtensionPeriod
		}

		l.cb(event.AggregateID(), "ObjectionStatusDetermined", eventData)

	case *ObjectionAdmissibilityDetermined:
		eventData := make(map[string]any)
		if data.Admissible != nil {
			eventData["admissible"] = *data.Admissible
		}

		l.cb(event.AggregateID(), "ObjectionAdmissibilityDetermined", eventData)
	case *AppealStatusDetermined:
		eventData := make(map[string]any)
		if data.Possible != nil {
			eventData["possible"] = *data.Possible
		}
		if data.NotPossibleReason != nil {
			eventData["not_possible_reason"] = *data.NotPossibleReason
		}
		if data.AppealPeriod != nil {
			eventData["appeal_period"] = *data.AppealPeriod
		}
		if data.DirectAppeal != nil {
			eventData["direct_appeal"] = *data.DirectAppeal
		}
		if data.DirectAppealReason != nil {
			eventData["direct_appeal_reason"] = *data.DirectAppealReason
		}
		if data.CompetentCourt != nil {
			eventData["competent_court"] = *data.CompetentCourt
		}
		if data.CourtType != nil {
			eventData["court_type"] = *data.CourtType
		}

		l.cb(event.AggregateID(), "AppealStatusDetermined", eventData)
	}

	return nil
}
