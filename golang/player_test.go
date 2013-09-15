package main

import (
	"testing"
)

func TestAddItems(t *testing.T) {
	items := Items{1: 10, 2: 20}
	itemAdd := []ItemInfo{
		{1, 10},
		{2, 20},
		{3, 33},
	}
	addItems(items, itemAdd)
	if items[1] != 20 || items[2] != 40 || items[3] != 33 {
		t.Fail()
	}
}
