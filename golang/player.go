package main

import (
	"fmt"
	//"github.com/golang/glog"
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
                        	WHERE userId=?`, session.UserId)
	var general, temp, social uint32
	err = row.Scan(&general, &temp, &social)
	lwutil.CheckError(err, "")

	//login reward
	loginRewardId := uint32(0)
	nextRewardRemain := uint32(0)

	type loginRewardInfo struct {
		LastTime int64
		Days     uint32
	}
	var lrInfo loginRewardInfo
	key := fmt.Sprintf("loginReward/%d", session.UserId)
	_, err = lwutil.GetKvDb(key, &lrInfo)
	lwutil.CheckError(err, "")
	now := lwutil.GetRedisTime()

	lastTime := time.Unix(lrInfo.LastTime, 0)
	year, month, day := lastTime.Date()
	currYear, currMonth, currDay := now.Date()
	if year != currYear || month != currMonth || day != currDay {
		lrInfo.LastTime = now.Unix()
		lrInfo.Days += 1

		lwutil.SetKvDb(key, &lrInfo)

		arrayLen := len(arrayLoginReward)
		for i, reward := range arrayLoginReward {
			if lrInfo.Days == reward.LoginNum {
				loginRewardId = reward.Id
				if i < arrayLen-1 {
					nextRewardRemain = arrayLoginReward[i+1].LoginNum - reward.LoginNum
				}
				protoAndLvs := []cardProtoAndLevel{
					{reward.RewardCardsID, 1},
				}

				//
				createCards(session.UserId, protoAndLvs, 0, WAGON_INDEX_GENERAL, STR_LOGIN_REWARD)

				break
			} else if lrInfo.Days > reward.LoginNum {
				break
			}
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
