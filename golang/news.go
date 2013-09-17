package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"fmt"
	"github.com/henyouqian/lwutil"
	"net/http"
)

func newsList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")
	w.Write(newsReply)
}

func newsRead(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	//session, err := findSession(w, r)
	//lwutil.CheckError(err, "err_auth")

	//input
	var in struct {
		NewsId uint32
	}
	err := lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	//find info
	row, ok := tblNews[fmt.Sprintf("%d", in.NewsId)]
	if !ok {
		lwutil.SendError("err_newsid", fmt.Sprintf("newsId=%d", in.NewsId))
	}

	//output
	type NC struct {
		Content string `json:"content"`
		PicUrl  string `json:"picUrl"`
	}
	var out struct {
		NewsContent NC `json:"newsContent"`
	}
	out.NewsContent.Content = row.NewsContent
	out.NewsContent.PicUrl = row.PicUrl

	lwutil.WriteResponse(w, out)
}

func regStore() {
	http.Handle("/whapi/news/list", lwutil.ReqHandler(newsList))
	http.Handle("/whapi/news/read", lwutil.ReqHandler(newsRead))
}
