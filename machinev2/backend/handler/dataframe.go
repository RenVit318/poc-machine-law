package handler

import (
	"context"
	"fmt"

	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

// SetSourceDataFrame implements api.StrictServerInterface.
func (handler *Handler) SetSourceDataFrame(ctx context.Context, request api.SetSourceDataFrameRequestObject) (api.SetSourceDataFrameResponseObject, error) {
	df := model.DataFrame{
		Service: request.Body.Data.Service,
		Table:   request.Body.Data.Table,
		Data:    request.Body.Data.Data,
	}

	if err := handler.servicer.SetSourceDataFrame(ctx, df); err != nil {
		return api.SetSourceDataFrame400JSONResponse{
			BadRequestErrorResponseJSONResponse: NewBadRequestErrorResponseObject(fmt.Errorf("set source dataframe: %w", err)),
		}, nil
	}

	return api.EmptyResponseResponse{}, nil
}
