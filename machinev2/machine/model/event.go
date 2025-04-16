package model

import (
	"time"

	"github.com/google/uuid"
)

// Event represents an event in the system
type Event struct {
	CaseID    uuid.UUID      `json:"case_id"`
	Timestamp time.Time      `json:"timestamp"`
	EventType string         `json:"event_type"`
	Data      map[string]any `json:"data"`
}

func (e Event) ToMap() map[string]any {
	return map[string]any{
		"case_id":    e.CaseID,
		"timestamp":  e.CaseID,
		"event_type": e.CaseID,
		"data":       e.Data,
	}
}
