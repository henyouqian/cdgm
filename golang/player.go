package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"github.com/henyouqian/lwutil"
)

type ItemInfo struct {
	Id    uint8
	Count uint32
}

type Items map[uint8]uint32

func addItems(items Items, adding []ItemInfo) {
	for _, v := range adding {
		items[v.Id] += v.Count
	}
}

type Band struct {
	Formation uint32
	Members   []uint64
}

func cardCollect(userId uint32, cardIds []uint32) error {
	rc := redisPool.Get()
	defer rc.Close()

	lwutil.GetKV("bbb", "ccc", nil)
	return nil
}
