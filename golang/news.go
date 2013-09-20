package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"encoding/json"
	"fmt"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"sort"
)

func newsList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//
	v, err := lwutil.GetKV(fmt.Sprintf("readList/%d", session.Userid), rc)
	lwutil.CheckError(err, "err_kv")
	if v == nil {
		v = []byte("[]")
	}

	var readList []uint32
	err = json.Unmarshal(v, &readList)
	lwutil.CheckError(err, "")

	type News struct {
		NewsId   uint32 `json:"newsId"`
		IsUnread bool   `json:"isUnread"`
		Date     string `json:"date"`
		Title    string `json:"title"`
	}

	newsList := make([]News, 0, 8)
	for _, v := range tblNewsList {
		isUnread := true
		for _, r := range readList {
			if v.Id == r {
				isUnread = false
				break
			}
		}

		news := News{
			v.Id,
			isUnread,
			v.Date,
			v.Title,
		}
		newsList = append(newsList, news)
	}

	//reverse
	for i, j := 0, len(newsList)-1; i < j; i, j = i+1, j-1 {
		newsList[i], newsList[j] = newsList[j], newsList[i]
	}

	type NewReply struct {
		News []News `json:"news"`
	}
	newsRp := NewReply{newsList}

	lwutil.WriteResponse(w, newsRp)
}

func newsRead(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//input
	var in struct {
		NewsId int
	}
	err = lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	//find info
	row, ok := tblNews[fmt.Sprintf("%d", in.NewsId)]
	if !ok {
		lwutil.SendError("err_newsid", fmt.Sprintf("newsId=%d", in.NewsId))
	}

	//record read id
	v, err := lwutil.GetKV(fmt.Sprintf("readList/%d", session.Userid), rc)
	lwutil.CheckError(err, "err_kv")
	var readList []int
	if v != nil {
		err = json.Unmarshal(v, &readList)
		lwutil.CheckError(err, "")
	}
	readList = append(readList, in.NewsId)

	//sort and truncate
	sort.Sort(sort.Reverse(sort.IntSlice(readList)))
	if len(readList) > MAX_NEWS {
		readList = readList[:MAX_NEWS]
	}

	//
	s, err := json.Marshal(&readList)
	lwutil.CheckError(err, "")

	err = lwutil.SetKV(fmt.Sprintf("readList/%d", session.Userid), s, rc)
	lwutil.CheckError(err, "err_kv")

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
