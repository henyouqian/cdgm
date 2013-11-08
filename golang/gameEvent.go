package main

import (
	"encoding/json"
	"github.com/garyburd/redigo/redis"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"time"
)

type GameEventInfo struct {
	EvtType   uint32
	NewsId    uint32
	StartTime int64
	EndTime   int64
}

type GameEventHttp struct {
	EvtType   uint32
	NewsId    uint32
	StartTime string
	EndTime   string
}

func setEventInfo(rc redis.Conn, evt *GameEventInfo) error {
	js, err := json.Marshal(evt)
	if err != nil {
		return lwutil.NewErr(err)
	}
	_, err = rc.Do("set", "gameEventInfo", js)
	if err != nil {
		return lwutil.NewErr(err)
	}
	return nil
}

func getEventInfo(rc redis.Conn) (*GameEventInfo, error) {
	bt, err := redis.Bytes(rc.Do("get", "gameEventInfo"))
	if err != nil {
		return nil, lwutil.NewErr(err)
	}

	var gameEventInfo GameEventInfo

	err = json.Unmarshal(bt, &gameEventInfo)
	if err != nil {
		return nil, lwutil.NewErr(err)
	}

	return &gameEventInfo, nil
}

func httpSetEventInfo(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	//in
	var in GameEventHttp
	err := lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	rc := redisPool.Get()
	defer rc.Close()

	startTime, err := time.ParseInLocation("2006-01-02 15:04:05", in.StartTime, time.Local)
	lwutil.CheckError(err, "err_invalid_time_format")
	endTime, err := time.ParseInLocation("2006-01-02 15:04:05", in.EndTime, time.Local)
	lwutil.CheckError(err, "err_invalid_time_format")

	if startTime.Unix() >= endTime.Unix() {
		lwutil.SendError("err_time", "")
	}

	evt := GameEventInfo{
		in.EvtType,
		in.NewsId,
		startTime.Unix(),
		endTime.Unix(),
	}
	setEventInfo(rc, &evt)

	//out
	lwutil.WriteResponse(w, "ok")
}

func httpGetEventInfo(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	rc := redisPool.Get()
	defer rc.Close()

	evt, err := getEventInfo(rc)
	lwutil.CheckError(err, "")

	beginTime := time.Unix(evt.StartTime, 0)
	endTime := time.Unix(evt.EndTime, 0)

	evtHttp := GameEventHttp{
		evt.EvtType,
		evt.NewsId,
		beginTime.Format("2006-01-02 15:04:05"),
		endTime.Format("2006-01-02 15:04:05"),
	}

	//out
	lwutil.WriteResponse(w, evtHttp)
}

func regGameEvent() {
	http.Handle("/goapi/gameevent/set", lwutil.ReqHandler(httpSetEventInfo))
	http.Handle("/goapi/gameevent/get", lwutil.ReqHandler(httpGetEventInfo))
}
