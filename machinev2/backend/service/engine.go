package service

import (
	"context"
)

// ResetEngine implements Servicer.
func (service *Service) ResetEngine(ctx context.Context) error {
	service.service.Reset()

	service.setInput()

	return nil
}
