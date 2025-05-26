package adapter

import (
	"github.com/minbzk/poc-machine-law/machinev2/backend/interface/api"
	"github.com/minbzk/poc-machine-law/machinev2/backend/model"
)

func FromEvent(event model.Event) api.Event {
	return api.Event{
		EventType: event.EventType,
		Timestamp: event.Timestamp,
		Data:      event.Data,
	}
}

func FromEvents(events []model.Event) []api.Event {
	items := make([]api.Event, 0, len(events))

	for idx := range events {
		items = append(items, FromEvent(events[idx]))
	}

	return items
}
