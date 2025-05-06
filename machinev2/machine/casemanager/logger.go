package casemanager

import (
	"context"

	eh "github.com/looplab/eventhorizon"
	"github.com/minbzk/poc-machine-law/machinev2/machine/internal/logging"
)

// LoggingMiddleware is a tiny command handle middleware for logging.
func LoggingMiddleware(logger logging.Logger) func(h eh.CommandHandler) eh.CommandHandler {
	return func(h eh.CommandHandler) eh.CommandHandler {
		return eh.CommandHandlerFunc(func(ctx context.Context, cmd eh.Command) error {
			logger.Error(ctx, "command handler", logging.NewField("commandType", cmd.CommandType()), logging.NewField("itemId", cmd.AggregateID()), logging.NewField("itemType", cmd.AggregateType()))
			return h.HandleCommand(ctx, cmd)
		})
	}
}

// Logger is a simple event handler for logging all events.
type Logger struct {
	logger logging.Logger
}

func NewLogger(logger logging.Logger) *Logger {
	return &Logger{
		logger: logger,
	}
}

// HandlerType implements the HandlerType method of the eventhorizon.EventHandler interface.
func (l *Logger) HandlerType() eh.EventHandlerType {
	return "logger"
}

// HandleEvent implements the HandleEvent method of the EventHandler interface.
func (l *Logger) HandleEvent(ctx context.Context, event eh.Event) error {
	l.logger.Error(ctx, "handle event", logging.NewField("eventType", event.EventType()), logging.NewField("itemId", event.AggregateID()), logging.NewField("itemType", event.AggregateType()), logging.NewField("event", event.Data()))
	return nil
}
