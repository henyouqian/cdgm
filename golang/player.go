package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"github.com/golang/glog"
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
	Id           uint32
	LastZoneId   uint32
	WarlordLevel uint16
	Bands        []struct {
		Formation uint32
	}
}

func checkTaskComplete(taskRow *rowTask, s *playerStatistics, i *playerInfoForTask) (isComplete bool, num, targetNum uint32) {
	switch taskRow.Type {
	case 1:
		if i.LastZoneId > taskRow.Target {
			return true, 1, 1
		}
		return false, 0, 1
	case 2:
		if uint32(i.WarlordLevel) >= taskRow.Target {
			return true, uint32(i.WarlordLevel), taskRow.Target
		}
		return false, uint32(i.WarlordLevel), taskRow.Target
	case 3:
		//fixme
		return false, 0, 0
	case 4:
		//fixme
		return false, 0, 0
	case 5:
		var timesRestrict TimesRestrict
		key := fmt.Sprintf("instTimesRst/user=%d&inst=%d", i.Id, taskRow.Detail)
		_, err := lwutil.GetKv(key, &timesRestrict, nil)
		lwutil.CheckError(err, "")
		if timesRestrict.TotalTimes >= taskRow.Target {
			return true, timesRestrict.TotalTimes, taskRow.Target
		}
		return false, timesRestrict.TotalTimes, taskRow.Target
	case 6:

		return false, 0, 0
	case 7:
		return false, 0, 0
	case 8:
		return false, 0, 0
	case 9:
		return false, 0, 0
	case 10:
		return false, 0, 0
	case 11:
		return false, 0, 0
	case 12:
		return false, 0, 0
	case 13:
		return false, 0, 0
	default:
		return false, 0, 0
	}

	return false, 0, 0
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
	row := whDB.QueryRow(`SELECT wagonGeneral, wagonTemp, wagonSocial,
		lastZoneId, c.level, bands
		FROM playerInfos JOIN cardEntities AS c ON warLord = c.id
		WHERE userId=?`, session.UserId)
	var general, temp, social uint32
	var pi playerInfoForTask
	var bands []byte
	pi.Id = session.UserId
	err = row.Scan(&general, &temp, &social, &pi.LastZoneId, &pi.WarlordLevel, &bands)
	lwutil.CheckError(err, fmt.Sprintf("userId=%d", session.UserId))

	json.Unmarshal(bands, &pi.Bands)

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
	type Reward struct {
		Id  int32  `json:"id"`
		Num uint32 `json:"num"`
	}
	type FinishedTask struct {
		TaskId  uint16   `json:"taskId"`
		Name    string   `json:"name"`
		Rewards []Reward `json:"rewards"`
	}
	fts := make([]FinishedTask, 0, 8)

	type CurrentTask struct {
		TaskId     uint16   `json:"taskId"`
		TotalNum   uint32   `json:"totalNum"`
		CurrentNum uint32   `json:"currentNum"`
		Name       string   `json:"name"`
		Comment    string   `json:"comment"`
		Content    string   `json:"content"`
		Rewards    []Reward `json:"rewards"`
	}

	checkTask := func(taskId uint16) *CurrentTask {
		var taskRow rowTask
		var num, targetNum uint32
		for true {
			t, ok := tblTask[strconv.Itoa(int(taskId))]
			taskRow = t
			if !ok {
				return &CurrentTask{}
			}
			complete, n1, n2 := checkTaskComplete(&taskRow, &u, &pi)
			num = n1
			targetNum = n2
			if complete {
				fTask := FinishedTask{
					TaskId:  taskId,
					Name:    taskRow.Name,
					Rewards: make([]Reward, 0, 3),
				}
				if taskRow.Reward1 != 0 {
					fTask.Rewards = append(fTask.Rewards, Reward{taskRow.Reward1, taskRow.Amount1})
				}
				if taskRow.Reward2 != 0 {
					fTask.Rewards = append(fTask.Rewards, Reward{taskRow.Reward2, taskRow.Amount2})
				}
				if taskRow.Reward3 != 0 {
					fTask.Rewards = append(fTask.Rewards, Reward{taskRow.Reward3, taskRow.Amount3})
				}
				//fixme: add rewards
				fts = append(fts, fTask)
				taskId++
			} else {
				break
			}
		}

		//current task
		glog.Infoln(taskRow)
		currTask := CurrentTask{
			TaskId:     taskId,
			TotalNum:   targetNum,
			CurrentNum: num,
			Name:       taskRow.Name,
			Comment:    taskRow.Comment,
			Content:    taskRow.Content,
			Rewards:    make([]Reward, 0, 3),
		}
		if taskRow.Reward1 != 0 {
			currTask.Rewards = append(currTask.Rewards, Reward{taskRow.Reward1, taskRow.Amount1})
		}
		if taskRow.Reward2 != 0 {
			currTask.Rewards = append(currTask.Rewards, Reward{taskRow.Reward2, taskRow.Amount2})
		}
		if taskRow.Reward3 != 0 {
			currTask.Rewards = append(currTask.Rewards, Reward{taskRow.Reward3, taskRow.Amount3})
		}

		return &currTask
	}

	////task1
	task1 := checkTask(u.CurrTask1)

	////task2
	task2 := checkTask(u.CurrTask2)

	////update task completion
	isNew := false
	if task1.TaskId != u.CurrTask1 || task2.TaskId != u.CurrTask2 {
		_, err = whDB.Exec("UPDATE playerStatistics SET currTask1=?, currTask2=?", task1, task2)
		lwutil.CheckError(err, "")
		isNew = true
	}

	currentTasks := make([]*CurrentTask, 0, 2)
	if task1.TaskId != 0 {
		currentTasks = append(currentTasks, task1)
	}
	if task2.TaskId != 0 {
		currentTasks = append(currentTasks, task2)
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
		"currentTask":      currentTasks,
		"finishTask":       fts,
	}

	lwutil.WriteResponse(w, &out)
}

func regPlayer() {
	http.Handle("/whapi/player/returnhomeinfo", lwutil.ReqHandler(returnHomeInfo))
}
