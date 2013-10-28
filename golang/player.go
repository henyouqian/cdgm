package main

import (
	"fmt"
	//"github.com/golang/glog"
	"database/sql"
	"github.com/henyouqian/lwutil"
	"net/http"
	"strconv"
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

type playerStatistics struct {
	CurrTask1, CurrTask2, PvpTotal, PvpMaxWin,
	Sacrifice, Evolution, GetCardS, GetCardA, GetCardB, GetCardC, GetCardD,
	CardS, CardA, CardB, CardC, CardD, CrystalHp, CrystalAtk, CrystalDef, CrystalWis, CrystalAgi,
	StoneBase, StoneMid, StoneAdv uint16
}

type playerInfoForTask struct {
	InZoneId     uint32
	WarlordLevel uint16
}

func checkTaskComplete(taskId uint16, s *playerStatistics) bool {
	taskRow, ok := tblTask[strconv.Itoa(int(taskId))]
	if !ok {
		return false
	}
	switch taskRow.Type {
	case 1:

		return false
	case 2:
		return false
	case 3:
		return false
	case 4:
		return false
	case 5:
		return false
	case 6:
		return false
	case 7:
		return false
	case 8:
		return false
	case 9:
		return false
	case 10:
		return false
	case 11:
		return false
	case 12:
		return false
	case 13:
		return false
	default:
		return false
	}

	return false
}

func returnHomeInfo(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//login reward
	loginRewardId := uint32(0)
	nextRewardRemain := uint32(0)

	type loginRewardInfo struct {
		LastTime int64
		Days     uint32
	}
	var lrInfo loginRewardInfo
	key := fmt.Sprintf("loginRewafrd/%d", session.UserId)
	exist, err := lwutil.GetKvDb(key, &lrInfo)
	lwutil.CheckError(err, "")
	now := lwutil.GetRedisTime()

	lastTime := time.Unix(lrInfo.LastTime, 0)
	year, month, day := lastTime.Date()
	currYear, currMonth, currDay := now.Date()
	if year != currYear || month != currMonth || day != currDay {
		lrInfo.LastTime = now.Unix()
		if !exist {
			lrInfo.Days = 0
		} else {
			lrInfo.Days += 1
		}

		lwutil.SetKvDb(key, &lrInfo)

		arrayLen := len(arrayLoginReward)
		for i, reward := range arrayLoginReward {
			if reward.LoginNum == lrInfo.Days {
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
			} else if reward.LoginNum > lrInfo.Days {
				break
			}
		}
	}

	//get wagon item count
	row := whDB.QueryRow(`SELECT wagonGeneral, wagonTemp, wagonSocial 
						FROM playerInfos
                        	WHERE userId=?`, session.UserId)
	var general, temp, social uint32
	err = row.Scan(&general, &temp, &social)
	lwutil.CheckError(err, fmt.Sprintf("userId=%d", session.UserId))

	//task
	row = whDB.QueryRow(`SELECT currTask1, currTask2, pvpTotal, pvpMaxWin, 
		sacrifice, evolution, getCardS, getCardA, getCardB, getCardC, getCardD,
		cardS, cardA, cardB, cardC, cardD, crystalHp, crystalAtk, crystalDef, crystalWis, crystalAgi,
		stoneBase, stoneMid, stoneAdv
		FROM playerStatistics
		WHERE userId=?`, session.UserId)

	var u playerStatistics

	err = row.Scan(&u.CurrTask1, &u.CurrTask2, &u.PvpTotal, &u.PvpMaxWin,
		&u.Sacrifice, &u.Evolution, &u.GetCardS, &u.GetCardA, &u.GetCardB, &u.GetCardC, &u.GetCardD,
		&u.CardS, &u.CardA, &u.CardB, &u.CardC, &u.CardD, &u.CrystalHp, &u.CrystalAtk, &u.CrystalDef, &u.CrystalWis, &u.CrystalAgi,
		&u.StoneBase, &u.StoneMid, &u.StoneAdv)
	if err == sql.ErrNoRows {
		u.CurrTask1 = 1001
		u.CurrTask2 = 2001
		_, err = whDB.Exec("INSERT INTO playerStatistics (userId, currTask1, currTask2) VALUES(?, ?, ?)",
			session.UserId, u.CurrTask1, u.CurrTask2)
		lwutil.CheckError(err, "")
	}

	///check task completion
	finishTask := make([]uint16, 0, 8)
	////task1
	task1 := u.CurrTask1
	for true {
		if checkTaskComplete(task1, &u) {
			finishTask = append(finishTask, task1)
			task1++
		} else {
			break
		}
	}
	////task2
	task2 := u.CurrTask2
	for true {
		if checkTaskComplete(task2, &u) {
			finishTask = append(finishTask, task2)
			task2++
		} else {
			break
		}
	}
	////update task completion
	isNew := false
	if task1 != u.CurrTask1 || task2 != u.CurrTask2 {
		_, err = whDB.Exec("UPDATE playerStatistics SET currTask1=?, currTask2=?", task1, task2)
		lwutil.CheckError(err, "")
		isNew = true
	}

	//out
	out := map[string]interface{}{
		"error":            nil,
		"general":          general,
		"temp":             temp,
		"social":           social,
		"loginRewardId":    loginRewardId,
		"nextRewardRemain": nextRewardRemain,
		"isNew":            isNew,
		"currentTask":      []uint16{task1, task2},
		"finishTask":       finishTask,
	}

	lwutil.WriteResponse(w, &out)
}

func regPlayer() {
	http.Handle("/whapi/player/returnhomeinfo", lwutil.ReqHandler(returnHomeInfo))
}
