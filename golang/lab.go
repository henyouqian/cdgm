package main

import (
	//"database/sql"
	"encoding/json"
	"fmt"
	//"github.com/garyburd/redigo/redis"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"sort"
	"time"
)

func dbSimple(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	// db
	ids := make([]int64, 10)
	stmt, err := testDB.Prepare("INSERT INTO batchTest (a, b, c, d) VALUES (?, ?, ?, ?)")
	lwutil.CheckError(err, "")
	for i := 0; i < 10; i++ {
		res, err := stmt.Exec(1, 2, 3, 4)
		lwutil.CheckError(err, "")

		id, err := res.LastInsertId()
		lwutil.CheckError(err, "")

		ids[i] = id
	}

	lwutil.WriteResponse(w, ids)
}

func dbBatch(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	// db
	ids := make([]int64, 10)
	tx, err := testDB.Begin()
	lwutil.CheckError(err, "")
	stmt, err := tx.Prepare("INSERT INTO batchTest (a, b, c, d) VALUES (?, ?, ?, ?)")
	lwutil.CheckError(err, "")
	for i := 0; i < 10; i++ {
		res, err := stmt.Exec(1, 2, 3, 4)
		lwutil.CheckError(err, "")

		id, err := res.LastInsertId()
		lwutil.CheckError(err, "")

		ids[i] = id

		fmt.Println(id)
	}

	lwutil.WriteResponse(w, ids)

	err = tx.Commit()
	lwutil.CheckError(err, "")
}

func g() {
	glog.Infoln("g")
}

func s() {
	l := []int{3, 35, 23, 6, 22}
	sort.Sort(sort.Reverse(sort.IntSlice(l)))
	glog.Infoln(l)
}

func jsonCompStructVsMap() {
	type OutVec2 struct {
		X uint32
		Y uint32
	}
	type Out struct {
		Error            string  `json:"error"`
		ZoneId           uint32  `json:"zoneId"`
		StartPos         OutVec2 `json:"startPos"`
		GoalPos          OutVec2 `json:"goalPos"`
		CurrPos          OutVec2 `json:"currPos"`
		RedCase          uint32  `json:"redCase"`
		GoldCase         uint32  `json:"goldCase"`
		Objs             string  `json:"objs"`
		Events           string  `json:"events"`
		Band             string  `json:"band"`
		EnterDialogue    uint32  `json:"enterDialogue"`
		CompleteDialogue uint32  `json:"completeDialogue"`
		PlayerRank       uint32  `json:"playerRank"`
		PlayerScore      uint32  `json:"playerScore"`
		Xp               uint32  `json:"xp"`
		XpAddRemain      uint32  `json:"xpAddRemain"`
		Whcoin           uint32  `json:"whcoin"`
	}

	t := time.Now().UnixNano()
	for i := 0; i < 1000; i++ {
		out := map[string]interface{}{
			"error":            "",
			"zoneId":           11,
			"startPos":         OutVec2{1, 2},
			"goalPos":          OutVec2{1, 2},
			"currPos":          OutVec2{1, 2},
			"redCase":          11,
			"goldCase":         22,
			"objs":             "xx",
			"events":           "xx",
			"band":             "xx",
			"enterDialoguev":   11,
			"completeDialogue": 11,
			"playerRank":       0,
			"payerScore":       0,
			"xp":               44,
			"xpAddRemain":      33,
			"whcoin":           22,
		}
		json.Marshal(out)
	}
	t1 := time.Now().UnixNano()
	glog.Infoln(t1 - t)

	t = t1
	for i := 0; i < 1000; i++ {
		out := Out{
			Error:            "",
			ZoneId:           11,
			StartPos:         OutVec2{1, 2},
			GoalPos:          OutVec2{1, 2},
			CurrPos:          OutVec2{1, 2},
			RedCase:          11,
			GoldCase:         22,
			Objs:             "xx",
			Events:           "xx",
			Band:             "xx",
			EnterDialogue:    11,
			CompleteDialogue: 11,
			PlayerRank:       0,
			PlayerScore:      0,
			Xp:               44,
			XpAddRemain:      33,
			Whcoin:           22,
		}
		json.Marshal(out)

	}

	t1 = time.Now().UnixNano()
	glog.Infoln(t1 - t)
}

func kv() {
	rc := redisPool.Get()
	defer rc.Close()

	type s struct {
		A int
		B string
	}
	in := s{23, "ggg"}
	_ = in
	in2 := map[string]interface{}{
		"A": 555,
		"B": "bbb",
	}
	var out s
	lwutil.SetKv("aaa", &in2, rc)
	lwutil.GetKv("aaa", &out, rc)
	glog.Infoln(out)
}

func csv() {
	type TestData struct {
		Id     uint32
		Objid  int32
		Amount uint32
		Prob   float32 `csv:"prob%"`
		Test   uint32
	}
	var tbl map[string]TestData
	err := lwutil.LoadCsvMap("../data/test.csv", []string{"id"}, &tbl)
	glog.Infoln(err)
	glog.Infof("%+v", tbl)
}

func hkv() {
	type Info struct {
		Ap         uint32
		MaxAp      uint32
		UserId     uint32
		LastXpTime string
	}

	//hkvs := []lwutil.Hkv{
	//	{whDB, "playerInfos", "userId", 12, Info{22, "helen"}, nil},
	//	{whDB, "playerInfos", "userId", 111, Info{30, "liwei"}, nil},
	//}
	//lwutil.HSetKvs(hkvs)

	var liwei, helen, bb Info
	type zoneCache struct {
		ZoneCache string
	}

	var liweiZoneCache zoneCache

	hkvs := []lwutil.Hkv{
		{whDB, "playerInfos", "userId", 311, &liwei, nil},
		{whDB, "playerInfos", "userId", 58, &helen, nil},
		{whDB, "playerInfos", "userId", 19, &bb, nil},
		{whDB, "playerInfos", "userId", 12, &liweiZoneCache, nil},
	}
	lwutil.HGetKvs(hkvs)
	glog.Infof("\n%+v\n%+v\n%+v\n%+v", liwei, helen, bb, liweiZoneCache)
}

func lab() {
	//items := map[string]uint32{"1": 5}
	//adding := []ItemInfo{{1, 2}, {3, 4}, {18, 1}, {19, 1}, {20, 3}, {21, 4}, {25, 444}}
	//moneyAdd, redCase, goldCase, whCoin := addItems(items, adding)
	//glog.Infoln(items, moneyAdd, redCase, goldCase, whCoin)
}

func labRedis(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	rc := redisPool.Get()
	defer rc.Close()

	//
	err := func() error {
		tx, err := whDB.Begin()
		if err != nil {
			return lwutil.NewErr(err)
		}
		defer lwutil.EndTx(tx, &err)

		var ap uint32
		for i := 0; i < 10000; i++ {
			tx.QueryRow("SELECT ap FROM playerInfos WHERE userId=?", i).Scan(&ap)
		}

		return err
	}()

	lwutil.CheckError(err, "")

	//*out
	out := map[string]interface{}{
		"hkvs": nil,
	}
	lwutil.WriteResponse(w, out)
}

func regLab() {
	http.Handle("/lab/dbsimple", lwutil.ReqHandler(dbSimple))
	http.Handle("/lab/dbbatch", lwutil.ReqHandler(dbBatch))
	http.Handle("/lab/redis", lwutil.ReqHandler(labRedis))
}
