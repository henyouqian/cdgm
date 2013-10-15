package main

import (
	//_ "github.com/go-sql-driver/mysql"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
)

func addLog(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	rc := redisPool.Get()
	defer rc.Close()

	//input
	var in struct {
		UserId int64
		Type   uint32
		Text   string
	}
	err := lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	if in.Type == 0 || in.Text == "" {
		lwutil.SendError("err_args", "")
	}

	//out
	out := map[string]interface{}{
		"u": in.UserId,
	}
	lwutil.WriteResponse(w, out)
}

func regLog() {
	http.Handle("/addLog", lwutil.ReqHandler(addLog))
}
