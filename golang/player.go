package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"fmt"
	"github.com/henyouqian/lwutil"
	"net/http"
	"time"
)

type ItemInfo struct {
	Id    uint8
	Count uint32
}

type Items map[uint8]uint32

func addItems(items Items, adding []ItemInfo) {
	for _, v := range adding {
		items[v.Id] += v.Count
	}
}

type Band struct {
	Formation uint32
	Members   []uint64
}

func returnHomeInfo(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//get wagon item count
	row := whDB.QueryRow(`SELECT wagonGeneral, wagonTemp, wagonSocial 
						FROM playerInfos
                        	WHERE userId=%s`, session.UserId)
	var general, temp, social uint32
	err = row.Scan(&general, &temp, &social)
	lwutil.CheckError(err, "")

	//login reward
	loginRewardId := 0
	nextRewardRemain := 0

	type loginRewardInfo struct {
		LastTime int64
		Days     uint32
	}
	var lrInfo loginRewardInfo
	exist, err := lwutil.GetKvDb(fmt.Sprintf("loginReward/%d", session.UserId), &lrInfo)
	lwutil.CheckError(err, "")
	now := lwutil.GetRedisTime()

	if exist {
		lastTime := time.Unix(lrInfo.LastTime, 0)
		year, month, day := lastTime.Date()
		currYear, currMonth, currDay := now.Date()
		if year != currYear || month != currMonth || day != currDay {
			lrInfo.LastTime = now.Unix()
			lrInfo.Days += 1

			for _, reward := range arrayLoginReward {
				if lrInfo.Days == reward.LoginNum {
					//if reward.LoginNum =
					break
				} else if lrInfo.Days > reward.LoginNum {
					break
				}
			}
			//if lrInfo.Days
		}
	}

	//out
	out := map[string]interface{}{
		"error":            nil,
		"general":          general,
		"temp":             temp,
		"social":           social,
		"loginRewardId":    loginRewardId,
		"nextRewardRemain": nextRewardRemain,
		"isNew":            false,
		"currentTask":      []uint32{},
		"finishTask":       []uint32{},
	}

	lwutil.WriteResponse(w, &out)
}

func regPlayer() {
	http.Handle("/whapi/player/returnhomeinfo", lwutil.ReqHandler(returnHomeInfo))
}
