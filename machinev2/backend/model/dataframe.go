package model

type DataFrame struct {
	Service string
	Table   string
	Data    []map[string]any
}
