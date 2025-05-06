package handler

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
)

// ResetEngine implements api.StrictServerInterface.
func (handler *Handler) ResetEngine(ctx context.Context, request api.ResetEngineRequestObject) (api.ResetEngineResponseObject, error) {
	if err := handler.servicer.ResetEngine(ctx); err != nil {
		return api.ResetEngine400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("reset engine: %w", err)),
		}, nil
	}

	return api.EmptyResponseResponse{}, nil
}
