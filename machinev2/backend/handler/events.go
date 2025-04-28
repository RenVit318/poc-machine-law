package handler

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/handler/adapter"
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
)

// GetEvents implements api.StrictServerInterface.
func (handler *Handler) GetEvents(ctx context.Context, request api.GetEventsRequestObject) (api.GetEventsResponseObject, error) {
	events, err := handler.servicer.EventList(ctx)
	if err != nil {
		return api.GetEvents400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("event list: %w", err)),
		}, err
	}

	return api.GetEvents200JSONResponse{
		EventListResponseJSONResponse: api.EventListResponseJSONResponse{
			Data: adapter.FromEvents(events),
		},
	}, nil
}

// GetCaseCaseIDEvents implements api.StrictServerInterface.
func (handler *Handler) GetCaseCaseIDEvents(ctx context.Context, request api.GetCaseCaseIDEventsRequestObject) (api.GetCaseCaseIDEventsResponseObject, error) {
	events, err := handler.servicer.CaseEventList(ctx, request.CaseID)
	if err != nil {
		return api.GetCaseCaseIDEvents400JSONResponse{BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("case event list: %w}", err))}, nil
	}

	return api.GetCaseCaseIDEvents200JSONResponse{
		EventListResponseJSONResponse: api.EventListResponseJSONResponse{
			Data: adapter.FromEvents(events),
		},
	}, nil
}
