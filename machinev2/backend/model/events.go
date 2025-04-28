package model

import "time"

type Event struct {
	EventType string
	Timestamp time.Time
	Data      map[string]any
}
