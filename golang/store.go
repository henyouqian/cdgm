package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"fmt"
	"github.com/henyouqian/lwutil"
	"net/http"
)

func storeList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")
	w.Write(goodsReply)
}

func storeBuy(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	session, err := findSession(w, r)
	lwutil.CheckError(err, "err_auth")

	//input
	var in struct {
		GoodsId uint32
		Num     uint32
	}
	err = lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	//get price
	storeItem, ok := tblStore[fmt.Sprintf("%d", in.GoodsId)]
	if !ok {
		lwutil.SendError("err_param", fmt.Sprintf("item not exists: id=%d", in.GoodsId))
	}
	price := storeItem.Price * in.Num

	//check whCoin
	row := whDB.QueryRow("SELECT whCoin FROM playerInfos WHERE userId=?", session.Userid)
	var whCoin uint32
	err = row.Scan(&whCoin)
	lwutil.CheckError(err, "")

	if whCoin < price {
		lwutil.SendError("err_coin_not_enough", fmt.Sprintf("whCoin=%d, coinNeeded=%d", whCoin, price))
	}

	//buy
	func() {
		tx, err := whDB.Begin()
		lwutil.CheckError(err, "")
		defer lwutil.EndTx(tx, &err)
	}()

	//output
	lwutil.WriteResponse(w, whCoin)
}

func regNews() {
	http.Handle("/whapi/store/list", lwutil.ReqHandler(storeList))
	http.Handle("/whapi/store/buy", lwutil.ReqHandler(storeBuy))
}
