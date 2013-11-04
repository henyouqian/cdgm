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
	Id  uint32
	Num uint32
}

func addItems(items map[string]uint32, adding []ItemInfo) (moneyAdd, redCase, goldCase uint32) {
	for _, item := range adding {
		switch item.Id {
		case ITEM_ID_MONEY_BAG_SMALL:
			moneyAdd += 100
		case ITEM_ID_MONEY_BAG_BIG:
			moneyAdd += 1000
		case ITEM_ID_RED_CASE:
			redCase += item.Num
		case ITEM_ID_GOLD_CASE:
			goldCase += item.Num
		case ITEM_ID_MONEY:
			moneyAdd += item.Num
		default:
			items[strconv.Itoa(int(item.Id))] += item.Num
		}
	}

	return moneyAdd, redCase, goldCase
}

type Band struct {
	Formation uint32
	Members   []uint64
}

type playerStatistics struct {
	CurrTask1, CurrTask2, PvpTotal, PvpMaxWin,
	Sacrifice, Evolution, GetCardS, GetCardA, GetCardB,
	CrystalHp, CrystalAtk, CrystalDef, CrystalWis, CrystalAgi,
	StoneBase, StoneMid, StoneAdv uint16
}

type playerInfoForTask struct {
	UserId       uint32
	LastZoneId   uint32
	WarlordLevel uint16
	Bands        []struct {
		Formation uint32
	}
}

func checkTaskComplete(taskRow *rowTask, s *playerStatistics, i *playerInfoForTask) (isComplete bool, num, targetNum uint32) {
	switch taskRow.Type {
	case 1:
		glog.Infoln(i.LastZoneId, taskRow.Target)
		if i.LastZoneId > taskRow.Target {
			return true, 1, 1
		}
		return false, 0, 1
	case 2:
		cmpNum := uint32(i.WarlordLevel)
		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		}
		return false, cmpNum, taskRow.Target
	case 3:
		cmpNum := uint32(s.PvpTotal)
		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		}
		return false, cmpNum, taskRow.Target
	case 4:
		cmpNum := uint32(s.PvpMaxWin)
		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		}
		return false, cmpNum, taskRow.Target
	case 5:
		var timesRestrict TimesRestrict
		key := fmt.Sprintf("instTimesRst/user=%d&inst=%d", i.UserId, taskRow.Detail)
		_, err := lwutil.GetKv(key, &timesRestrict, nil)
		lwutil.CheckError(err, "")
		if timesRestrict.TotalTimes >= taskRow.Target {
			return true, timesRestrict.TotalTimes, taskRow.Target
		}
		return false, timesRestrict.TotalTimes, taskRow.Target
	case 6:
		for _, band := range i.Bands {
			if band.Formation == taskRow.Target {
				return true, 1, 1
			}
		}
		return false, 0, 1
	case 7:
		return false, 0, 0
	case 8:
		if uint32(s.Sacrifice) >= taskRow.Target {
			return true, uint32(s.Sacrifice), taskRow.Target
		}
		return false, uint32(s.Sacrifice), taskRow.Target
	case 9:
		if uint32(s.Evolution) >= taskRow.Target {
			return true, uint32(s.Evolution), taskRow.Target
		}
		return false, uint32(s.Evolution), taskRow.Target
	case 10:
		var cmpNum uint32
		switch taskRow.Detail {
		case 1:
			cmpNum = uint32(s.CrystalHp)
		case 2:
			cmpNum = uint32(s.CrystalAtk)
		case 3:
			cmpNum = uint32(s.CrystalDef)
		case 4:
			cmpNum = uint32(s.CrystalWis)
		case 5:
			cmpNum = uint32(s.CrystalAgi)
		case 0:
			cmpNum = uint32(s.CrystalHp + s.CrystalAtk + s.CrystalDef + s.CrystalWis + s.CrystalAgi)
		default:
			glog.Errorf("invalid taskRow.Detail: taskRow = %+v", taskRow)
		}

		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		} else {
			return false, cmpNum, taskRow.Target
		}

	case 11:
		var cmpNum uint32
		switch taskRow.Detail {
		case 1:
			cmpNum = uint32(s.GetCardB)
		case 2:
			cmpNum = uint32(s.GetCardA)
		case 3:
			cmpNum = uint32(s.GetCardS)
		case 0:
			cmpNum = uint32(s.GetCardB + s.GetCardA + s.GetCardS)
		default:
			glog.Errorf("invalid taskRow.Detail: taskRow = %+v", taskRow)
		}

		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		} else {
			return false, cmpNum, taskRow.Target
		}

	case 12:
		var collectedCards []uint32
		key := fmt.Sprintf("cardCollect/%d", i.UserId)
		_, err := lwutil.GetKvDb(key, &collectedCards)
		if err != nil {
			return false, 0, taskRow.Target
		}

		var numD, numC, numB, numA, numS uint32
		for _, protoId := range collectedCards {
			cardRow, ok := tblCard[strconv.Itoa(int(protoId))]
			if ok {
				switch cardRow.Rarity {
				case 1:
					numD++
				case 2:
					numC++
				case 3:
					numB++
				case 4:
					numA++
				case 5:
					numS++
				}
			}
		}

		var cmpNum uint32
		switch taskRow.Detail {
		case 1:
			cmpNum = numD
		case 2:
			cmpNum = numC
		case 3:
			cmpNum = numB
		case 4:
			cmpNum = numA
		case 5:
			cmpNum = numS
		case 0:
			cmpNum = numD + numC + numB + numA + numS
		default:
			glog.Errorf("invalid taskRow.Detail: taskRow = %+v", taskRow)
		}

		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		} else {
			return false, cmpNum, taskRow.Target
		}

	case 13:
		var cmpNum uint32
		switch taskRow.Detail {
		case 1:
			cmpNum = uint32(s.StoneBase)
		case 2:
			cmpNum = uint32(s.StoneMid)
		case 3:
			cmpNum = uint32(s.StoneAdv)
		case 0:
			cmpNum = uint32(s.StoneBase + s.StoneMid + s.StoneAdv)
		default:
			glog.Errorf("invalid taskRow.Detail: taskRow = %+v", taskRow)
		}

		if cmpNum >= taskRow.Target {
			return true, cmpNum, taskRow.Target
		} else {
			return false, cmpNum, taskRow.Target
		}

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

	//get player info
	row := whDB.QueryRow(`SELECT wagonGeneral, wagonTemp, wagonSocial,
		lastZoneId, c.level, bands, items, money
		FROM playerInfos JOIN cardEntities AS c ON warLord = c.id
		WHERE userId=?`, session.UserId)
	var general, temp, social uint32
	var pi playerInfoForTask
	var bands []byte
	var itemsRaw []byte
	var items map[string]uint32
	var money uint32
	pi.UserId = session.UserId
	err = row.Scan(&general, &temp, &social, &pi.LastZoneId, &pi.WarlordLevel, &bands, &itemsRaw, &money)
	lwutil.CheckError(err, fmt.Sprintf("userId=%d", session.UserId))

	json.Unmarshal(bands, &pi.Bands)
	json.Unmarshal(itemsRaw, &items)

	//task
	row = whDB.QueryRow(`SELECT currTask1, currTask2, pvpTotal, pvpMaxWin, 
		sacrifice, evolution, getCardS, getCardA, getCardB,
		crystalHp, crystalAtk, crystalDef, crystalWis, crystalAgi,
		stoneBase, stoneMid, stoneAdv
		FROM playerStatistics
		WHERE userId=?`, session.UserId)

	var u playerStatistics

	err = row.Scan(&u.CurrTask1, &u.CurrTask2, &u.PvpTotal, &u.PvpMaxWin,
		&u.Sacrifice, &u.Evolution, &u.GetCardS, &u.GetCardA, &u.GetCardB,
		&u.CrystalHp, &u.CrystalAtk, &u.CrystalDef, &u.CrystalWis, &u.CrystalAgi,
		&u.StoneBase, &u.StoneMid, &u.StoneAdv)
	if err == sql.ErrNoRows {
		u.CurrTask1 = 1001
		u.CurrTask2 = 2001
		_, err = whDB.Exec("INSERT INTO playerStatistics (userId, currTask1, currTask2) VALUES(?, ?, ?)",
			session.UserId, u.CurrTask1, u.CurrTask2)
		lwutil.CheckError(err, "")
	} else {
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
		Content string   `json:"content"`
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

	checkTask := func(taskId uint16) (task *CurrentTask, allFinished bool) {
		var taskRow rowTask
		var num, targetNum uint32
		cardsAdd := make([]cardProtoAndLevel, 0, 8)
		itemsAdd := make([]ItemInfo, 0, 8)
		for true {
			t, ok := tblTask[strconv.Itoa(int(taskId))]
			taskRow = t
			if !ok {
				return &CurrentTask{TaskId: taskId}, true
			}
			complete, n1, n2 := checkTaskComplete(&taskRow, &u, &pi)
			num = n1
			targetNum = n2
			if complete {
				fTask := FinishedTask{
					TaskId:  taskId,
					Name:    taskRow.Name,
					Content: taskRow.Content,
					Rewards: make([]Reward, 0, 3),
				}

				if taskRow.Reward1 != 0 {
					fTask.Rewards = append(fTask.Rewards, Reward{taskRow.Reward1, taskRow.Amount1})
					if taskRow.Reward1 > 0 {
						itemsAdd = append(itemsAdd, ItemInfo{uint32(taskRow.Reward1), taskRow.Amount1})
					} else if taskRow.Reward1 < 0 {
						cardsAdd = append(cardsAdd, cardProtoAndLevel{uint32(-taskRow.Reward1), 1})
					}
				}
				if taskRow.Reward2 != 0 {
					fTask.Rewards = append(fTask.Rewards, Reward{taskRow.Reward2, taskRow.Amount2})
					if taskRow.Reward2 > 0 {
						itemsAdd = append(itemsAdd, ItemInfo{uint32(taskRow.Reward2), taskRow.Amount2})
					} else if taskRow.Reward2 < 0 {
						cardsAdd = append(cardsAdd, cardProtoAndLevel{uint32(-taskRow.Reward2), 1})
					}
				}
				if taskRow.Reward3 != 0 {
					fTask.Rewards = append(fTask.Rewards, Reward{taskRow.Reward3, taskRow.Amount3})
					if taskRow.Reward3 > 0 {
						itemsAdd = append(itemsAdd, ItemInfo{uint32(taskRow.Reward3), taskRow.Amount3})
					} else if taskRow.Reward3 < 0 {
						cardsAdd = append(cardsAdd, cardProtoAndLevel{uint32(-taskRow.Reward3), 1})
					}
				}

				fts = append(fts, fTask)
				taskId++
			} else {
				break
			}
		}

		//add cards
		if len(cardsAdd) > 0 {
			_, err = createCards(session.UserId, cardsAdd, 0, WAGON_INDEX_GENERAL, STR_TASK_REWARD)
			lwutil.CheckError(err, "")
		}

		//add items
		if len(itemsAdd) > 0 {
			dMoney, _, _ := addItems(items, itemsAdd)
			money += dMoney
			jsItems, err := json.Marshal(items)
			lwutil.CheckError(err, "")

			_, err = whDB.Exec(`UPDATE playerInfos SET items=?, money=?
                WHERE userid=?`, jsItems, money, session.UserId)
			lwutil.CheckError(err, "")
		}

		//current task
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

		return &currTask, false
	}

	////task1
	task1, allFinished1 := checkTask(u.CurrTask1)

	////task2
	task2, allFinished2 := checkTask(u.CurrTask2)

	////update task completion
	isNew := false
	taskId1 := task1.TaskId
	taskId2 := task2.TaskId
	if taskId1 == 0 {
		taskId1 = u.CurrTask1
	}
	if taskId2 == 0 {
		taskId2 = u.CurrTask2
	}
	if taskId1 != u.CurrTask1 || taskId2 != u.CurrTask2 {
		_, err = whDB.Exec("UPDATE playerStatistics SET currTask1=?, currTask2=? WHERE userId=?", taskId1, taskId2, session.UserId)
		lwutil.CheckError(err, "")
		isNew = true
	}

	currentTasks := make([]*CurrentTask, 0, 2)
	if !allFinished1 {
		currentTasks = append(currentTasks, task1)
	}
	if !allFinished2 {
		currentTasks = append(currentTasks, task2)
	}

	//out
	out := map[string]interface{}{
		"error":            nil,
		"general":          general,
		"temp":             temp,
		"social":           social,
		"money":            money,
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
