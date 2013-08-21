package main

import (
	"github.com/garyburd/redigo/redis"
	"fmt"
	"time"
	"net/http"
	"net/url"
	"encoding/json"
)

const (
	desc = "pvp rank"
)

func sandRewardMain(){
	for {
		// 
		conn := redisPool.Get()
		defer conn.Close()
		
		// pop one from redis
		reply, err := redis.Bytes(conn.Do("rpop", "rewardEntities"))
		if err != nil {
			panic(err)
		}
		if len(reply) != 0 {
			var re RewardEntity
			err := json.Unmarshal(reply, &re)
			if err != nil {
				panic(err)
			}
			fmt.Println("re:", re)

			//add item or card
			urls := make([]string, 0, 10)
			if re.Reward.IsCard {
            	for i := 0; i < re.Reward.Count; i++ {
            		url := fmt.Sprintf("http://localhost/whapi/admin/addCardToWagon?userId=%d&protoId=%d&level=%d&desc=%s&secretcode=e468251e-932b-43e4-a35f-d0d80413d2b3",
						re.Userid, re.Reward.Id, 1, desc)
            		urls = append(urls, url)
            	}
			} else {
				url := fmt.Sprintf("http://localhost/whapi/admin/addItemToWagon?userId=%d&itemId=%d&itemNum=%d&desc=%s&secretcode=e468251e-932b-43e4-a35f-d0d80413d2b3",
						re.Userid, re.Reward.Id, re.Reward.Count, desc)
				urls = append(urls, url)
			}

			for _, v := range urls {
				reply, err := http.Get(url.QueryEscape(v))
				if err != nil {
					panic(err)
				}
				fmt.Println(reply)
			}
		}

		time.Sleep(50000 * time.Millisecond)
	}
}
