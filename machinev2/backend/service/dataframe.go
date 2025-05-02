package service

import (
	"context"

	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
	"github.com/minbzk/poc-machine-law/machinev2/machine/dataframe"
)

// SetSourceDataFrame implements Servicer.
func (service *Service) SetSourceDataFrame(ctx context.Context, df model.DataFrame) error {
	service.service.SetSourceDataFrame(df.Service, df.Table, dataframe.New(df.Data))

	return nil
}
