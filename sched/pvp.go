package main

import (
	"github.com/garyburd/redigo/redis"
	"fmt"
	"time"
	"encoding/csv"
	"encoding/json"
	"os"
	"log"
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
	if err != nil {
		panic(err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}

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

func pvpMain(){
	tbl := loadTbl()
	log.Println(tbl)
	
	for {
		// 
		conn := redisPool.Get()
		defer conn.Close()

		// get finished leaderboard
		t := time.Now().Unix()
		lbnames, err := redis.Strings(conn.Do("zrangebyscore", 
			"leaderboard_endtime_zsets", 0, t, "limit", 0, 10))
		if err != nil {
			panic(err)
		}

		// send rewards
		if len(lbnames) > 0 {
			lbname := lbnames[0]
			resultsKey := "leaderboard_result/"+lbname
			resultsKey = "leaderboard_result/"+"pvp"	//fixme

			maxRank := tbl[len(tbl)-1].Rank
			strUserIds, err := redis.Strings(conn.Do("zrange", resultsKey, 0, maxRank))
			strUserIds = []string{"12", "58", "59"}		//fixme
			if err != nil {
				panic(err)
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
		}

		log.Println("add pvp")
		
		time.Sleep(2000 * time.Millisecond)
	}
}
