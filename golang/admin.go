package main

import (
	//"github.com/garyburd/redigo/redis"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"time"
)

func httpGetAdminInfo(w http.ResponseWriter, r *http.Request) {
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
	out := map[string]interface{}{
		"GameEvent": evtHttp,
	}
	lwutil.WriteResponse(w, out)
}

func regAdmin() {
	http.Handle("/goapi/admin/getinfo", lwutil.ReqHandler(httpGetAdminInfo))
}
