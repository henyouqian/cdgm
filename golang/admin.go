package main

import (
	//"github.com/garyburd/redigo/redis"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"time"
)

func checkAdmin(session *Session) {
	if session.UserName != "admin" && session.UserName != "aa" {
		lwutil.SendError("err_permission", "")
	}
}

func httpGetAdminInfo(w http.ResponseWriter, r *http.Request) {
	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	checkAdmin(session)

	evt, err := getGameEventInfo(rc)
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
