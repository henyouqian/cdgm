package main

import (
	//"github.com/henyouqian/lwutil"
	"encoding/json"
	"github.com/golang/glog"
	"time"
)

var (
	currGameEvent GameEventInfo
)

type GameEventInfo struct {
	EvtType   uint32
	NewsId    uint32
	StartTime int64
	EndTime   int64
}

func setEventInfo() {
	startTime := time.Date(2013, 11, 5, 0, 0, 0, 0, time.Local).Unix()
	endTime := time.Date(2013, 12, 5, 0, 0, 0, 0, time.Local).Unix()
	currGameEvent = GameEventInfo{1, 2, startTime, endTime}

	rc := redisPool.Get()
	defer rc.Close()

	js, err := json.Marshal(currGameEvent)
	if err != nil {
		glog.Errorln(err)
	}
	_, err = rc.Do("set", "gameEventInfo", js)
	if err != nil {
		glog.Errorln(err)
	}
}
