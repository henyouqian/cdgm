package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"github.com/henyouqian/lwutil"
	"net/http"
)

func storeList(w http.ResponseWriter, r *http.Request) {
	//lwutil.CheckMathod(r, "POST")

	//session, err := findSession(w, r)
	//lwutil.CheckError(err, "err_auth")

	// reply
	w.Write(goodsReply)
}

func regAuth() {
	http.Handle("/whapi/store/list", lwutil.ReqHandler(storeList))
}
