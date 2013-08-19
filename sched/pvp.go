package main

import (
	"github.com/garyburd/redigo/redis"
	"fmt"
	"time"
	"strconv"
	"encoding/csv"
	"os"
)


var pool *redis.Pool


func init() {
	pool = &redis.Pool{
		MaxIdle: 5,
		IdleTimeout: 240 * time.Second,
		Dial: func () (redis.Conn, error) {
			c, err := redis.Dial("tcp", "localhost:6379")
			if err != nil {
				return nil, err
			}
			return c, err
		},
	}
}

type RewardObj struct {
	objtype int
	objid int
	objcount int
}

type RewardTbl map[int] []RewardObj

func atoi(str string) int {
	i, err := strconv.Atoi(str)
	if err != nil {
		panic(err)
	}
	return i
}

func (self RewardTbl) load() {
	f, err := os.Open("../data/pvpWinRewards.csv")
	if err != nil {
		panic(err)
	}
	defer f.Close()

	reader := csv.NewReader(f)
	records, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}

	for i, v := range(records) {
		if i == 0 {
			continue
		}
		obj := RewardObj{atoi(v[0]), atoi(v[1]), atoi(v[2])}

		wincount := atoi(v[3])
		_, exists := self[wincount]
		if exists {
			self[wincount] = append(self[wincount], obj)
		} else {
			self[wincount] = []RewardObj{obj}
		}
	}

	fmt.Println(self)
}


func pvpMain(){
	tbl := make(RewardTbl)
	tbl.load()

	for {
		// 
		conn := pool.Get()
		defer conn.Close()

		// get finished leaderboard
		t := time.Now().Unix()
		lbnames, err := redis.Strings(conn.Do("zrangebyscore", 
			"leaderboard_endtime_zsets", 0, t, "limit", 0, 10))
		if err != nil {
			fmt.Println("error: ", err)
			goto sleep
		}

		// send rewards
		if len(lbnames) > 0 {
			lbname := lbnames[0]
			resultsKey := "leaderboard_result/"+lbname
			resultsKey = "leaderboard_result/"+"pvp"

			strs, err := redis.Strings(conn.Do("zrange", resultsKey, 0, 30))
			if err != nil {
				fmt.Println("error: ", err)
				goto sleep
			}
			for i, str := range(strs) {
				userid, _ := strconv.Atoi(str)
				fmt.Println(i, userid)
			}
			
		}
		
		sleep:
			time.Sleep(2000 * time.Millisecond)
	}
}
