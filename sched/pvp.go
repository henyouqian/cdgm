package main

import (
	"github.com/garyburd/redigo/redis"
	"time"
	"encoding/csv"
	"encoding/json"
	"os"
	"github.com/golang/glog"
)


type RewardObj struct {
	IsCard bool
	Id int
	Count int
}


type RewardsPerRank struct {
	Rank int
	Rewards []RewardObj
}

type RewardTbl []RewardsPerRank

func loadTbl() RewardTbl {
	tbl := make([]RewardsPerRank, 0, 10)

	f, err := os.Open("../data/pvpRankRewards.csv")
	checkError(err)
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	checkError(err)

	colmap := make(map[string]int)

	currRank := 0
	for i, v := range records {
		if i == 0 {
			for colidx, colname := range v {
				colmap[colname] = colidx
			}
			continue
		}
		obj := RewardObj{atoi(v[colmap["type"]]) == 2, atoi(v[colmap["objectId"]]), atoi(v[colmap["count"]])}
		rank := atoi(v[colmap["rank"]])

		if rank != currRank {
			currRank = rank
			tbl = append(tbl, RewardsPerRank{rank, []RewardObj{obj}})
		} else {
			idx := len(tbl) - 1
			tbl[idx].Rewards = append(tbl[idx].Rewards, obj)
		}
	}
	return tbl
}


type RewardEntity struct{
	Userid int
	Reward RewardObj
}

func sendRewards(lbname string, conn redis.Conn, tbl RewardTbl) {
	resultsKey := "leaderboard_result/"+lbname

	maxRank := tbl[len(tbl)-1].Rank
	strUserIds, err := redis.Strings(conn.Do("zrange", resultsKey, 0, maxRank))
	// strUserIds = []string{"12", "58", "59"}		//fixme
	if err != nil {
		return
	}
	lastRank := 0
	rwdEntities := make([]RewardEntity, 0, maxRank)
	for _, rwds := range tbl {
		for rank := lastRank + 1; rank <= rwds.Rank; rank++ {
			if rank > len(strUserIds) {
				break;
			}
			userid := atoi(strUserIds[rank-1])
			lastRank = rank

			for _, rwd := range rwds.Rewards {
				rwdEntity := RewardEntity{userid, rwd}
				rwdEntities = append(rwdEntities, rwdEntity)
			}
		}
	}

	// add reward entities to redis
	jsonRwdEntities := make([][]byte, 0, len(rwdEntities))
	for _, re := range rwdEntities {
		j, err := json.Marshal(re)
		if err != nil {
			panic(err)
		}
		jsonRwdEntities = append(jsonRwdEntities, j)
	}

	for _, v := range jsonRwdEntities {
		conn.Send("lpush", "rewardEntities", v)
	}
	conn.Flush()
	_, err = conn.Receive()
	if err != nil {
		panic(err)
	}

	// clean the leaderboard
	conn.Send("rename", "leaderboard_result/pvp_temp", "leaderboard_result/pvp_yesterday")
	conn.Send("rename", "leaderboard_result_info/pvp_temp", "leaderboard_result_info/pvp_yesterday")
	conn.Flush()
}

func pvpMain(){
	tbl := loadTbl()
	
	for {
		// 
		conn := redisPool.Get()
		defer conn.Close()

		// get finished leaderboard
		t := time.Now().Unix()
		reply, err := conn.Do("zrangebyscore", 
			"leaderboard_endtime_zsets", 0, t, "limit", 0, 10)
		checkError(err)

		if reply == nil {
			glog.Info("no finished leaderboard, sleep 60 Sec...")
			time.Sleep(60 * time.Second)
			continue
		}

		lbnames, err := redis.Strings(reply, err)
		checkError(err)
		_ = lbnames

		// send rewards
		// for _, lbname := range lbnames {
		// 	sendRewards(lbname, conn)
		// }

		// just for pvp now
		// check pvp data time
		pvptimeRaw, err := conn.Do("get", "pvpDate")
		checkError(err)

		if pvptimeRaw == nil {
			glog.Info("create pvpDate")
			tt := time.Now()
			jst, _ := tt.MarshalJSON()
			conn.Do("set", "pvpDate", jst)
			continue
		}
		var pvptime time.Time
		pvptimeBytes, err := redis.Bytes(pvptimeRaw, err)
		checkError(err)
		err = pvptime.UnmarshalJSON(pvptimeBytes)
		checkError(err)

		y1, m1, d1 := pvptime.Date()
		
		tt := time.Now()
		y2, m2, d2 := tt.Date()

		// when date change
		if true || y1 != y2 || m1 != m2 || d1 != d2 {
			// 
			conn.Send("rename", "leaderboard_result/pvp", "leaderboard_result/pvp_temp")
			conn.Send("rename", "leaderboard_result_info/pvp", "leaderboard_result_info/pvp_temp")
			conn.Flush()

			//send rewards
			sendRewards("pvp_temp", conn, tbl)
		}

		time.Sleep(60 * time.Second)
	}
}
