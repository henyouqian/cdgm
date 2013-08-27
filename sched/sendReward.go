package main

import (
	"github.com/garyburd/redigo/redis"
	"log"
	"fmt"
	"time"
	"net/http"
	"net/url"
	"encoding/json"
)

var (
	description = url.QueryEscape("活動獎勵")
	wagon_desc string
)

func init() {
	
}


func sandRewardMain() {
	for {
		// 
		conn := redisPool.Get()
		defer conn.Close()
		
		// pop one from redis
		rawReply, err := conn.Do("rpop", "rewardEntities")
		checkError(err)

		if rawReply == nil {
			log.Println("no rewards to sent, sleep 10 Sec...")
			time.Sleep(10 * time.Second)
			continue
		}

		reply, err := redis.Bytes(rawReply, err)
		checkError(err)

		if len(reply) != 0 {
			var re RewardEntity
			err := json.Unmarshal(reply, &re)
			if err != nil {
				panic(err)
			}

			//add item or card
			urls := make([]string, 0, 10)
			if re.Reward.IsCard {
            	for i := 0; i < re.Reward.Count; i++ {
            		url := fmt.Sprintf("http://localhost/whapi/admin/addCardToWagon?userId=%d&protoId=%d&level=%d&desc=%s&secretcode=e468251e-932b-43e4-a35f-d0d80413d2b3",
						re.Userid, re.Reward.Id, 1, description)
            		urls = append(urls, url)
            	}
			} else {
				url := fmt.Sprintf("http://localhost/whapi/admin/addItemToWagon?userId=%d&itemId=%d&itemNum=%d&desc=%s&secretcode=e468251e-932b-43e4-a35f-d0d80413d2b3",
						re.Userid, re.Reward.Id, re.Reward.Count, description)
				urls = append(urls, url)
			}

			for _, v := range urls {
				r, err := http.Get(v)
				checkError(err)
				if r.StatusCode != 200 {
					log.Println("http get error: statusCode=", r.StatusCode)
					time.Sleep(10 * time.Second)
				} else {
					log.Printf("award sended ok: %+v\n", re)
				}
			}
		}

		time.Sleep(50 * time.Millisecond)
	}
}
