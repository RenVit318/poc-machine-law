package utils

import (
	"sync"
)

type key = string
type data = map[string]any

type RuleSpecCache struct {
	lookup map[key]data
	mu     sync.RWMutex
}

func NewRuleSpecCache() *RuleSpecCache {
	return &RuleSpecCache{
		lookup: make(map[key]data),
		mu:     sync.RWMutex{},
	}
}

func (c *RuleSpecCache) Get(key string) (data, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	d, ok := c.lookup[key]

	return d, ok
}

func (c *RuleSpecCache) Set(key key, data data) {
	c.mu.Lock()
	defer c.mu.Unlock()

	c.lookup[key] = data
}
