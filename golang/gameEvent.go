package main

import (
	//"github.com/henyouqian/lwutil"
	"time"
)

var (
	currGameEvent GameEventInfo
)

type GameEventInfo struct {
	evtType   uint32
	newsId    uint32
	startTime int64
	endTime   int64
}

func init() {
	startTime := time.Date(2013, 11, 5, 0, 0, 0, 0, time.Local).Unix()
	endTime := time.Date(2013, 12, 5, 0, 0, 0, 0, time.Local).Unix()
	currGameEvent = GameEventInfo{1, 2, startTime, endTime}
}
