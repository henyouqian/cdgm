package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"encoding/json"
	"fmt"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
)

func storeList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")
	w.Write(goodsReply)
}

func storeBuy(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	session, err := findSession(w, r, nil)
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

	//select from db
	row := whDB.QueryRow("SELECT whCoin, items FROM playerInfos WHERE userId=?", session.UserId)
	var whCoin uint32
	var itemsJs []byte
	err = row.Scan(&whCoin, &itemsJs)
	lwutil.CheckError(err, "")

	//check whCoin
	if whCoin < price {
		lwutil.SendError("err_coin_not_enough", fmt.Sprintf("whCoin=%d, coinNeeded=%d", whCoin, price))
	}
	whCoin -= price

	//add items
	var items map[string]uint32
	glog.Infoln(string(itemsJs))
	err = json.Unmarshal(itemsJs, &items)
	lwutil.CheckError(err, "")
	num := items[fmt.Sprintf("%d", storeItem.ItemId)]
	addNum := storeItem.Num * in.Num
	items[fmt.Sprintf("%d", storeItem.ItemId)] = num + addNum
	itemsJs, err = json.Marshal(items)
	lwutil.CheckError(err, "")

	//update db
	_, err = whDB.Exec("UPDATE playerInfos SET whCoin=?, items=? WHERE userId=?", whCoin, itemsJs, session.UserId)
	lwutil.CheckError(err, "")

	//output
	type rpItem struct {
		Id  uint32 `json:"id"`
		Num uint32 `json:"num"`
	}
	out := struct {
		Whcoin uint32   `json:"whcoin"`
		Items  []rpItem `json:"items"`
	}{
		whCoin,
		[]rpItem{{storeItem.ItemId, addNum}},
	}
	lwutil.WriteResponse(w, out)
}

func regNews() {
	http.Handle("/whapi/store/list", lwutil.ReqHandler(storeList))
	http.Handle("/whapi/store/buy", lwutil.ReqHandler(storeBuy))
}
