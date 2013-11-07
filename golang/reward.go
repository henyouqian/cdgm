package main

import (
	"github.com/garyburd/redigo/redis"
	"github.com/golang/glog"
	//"github.com/henyouqian/lwutil"
	"encoding/json"
	"time"
)

const (
	REWARD_LIST = "rewardList"
)

type Reward struct {
	ObjId  int32
	Num    uint32
	UserId uint32
	Desc   string
}

func sendRewardTask() {
	rc := redisPool.Get()
	defer rc.Close()

	rewardsValues, err := redis.Values(rc.Do("lrange", REWARD_LIST, 0, 99))
	if err != nil {
		glog.Errorln(err)
		time.Sleep(time.Second)
		return
	}
	rewardsNum := len(rewardsValues)
	_ = rewardsNum

	for _, v := range rewardsValues {
		bytes, err := redis.Bytes(v, nil)
		if err != nil {
			glog.Errorln(err)
			continue
		}
		var reward Reward
		err = json.Unmarshal(bytes, &reward)
		if err != nil {
			glog.Errorln(err)
			continue
		}

		protoAndLvs := make([]cardProtoAndLevel, 0, 64)

		if reward.ObjId < 0 { //card
			cardProto := uint32(reward.ObjId)
			for i := uint32(0); i < reward.Num; i++ {
				protoAndLvs = append(protoAndLvs, cardProtoAndLevel{cardProto, 1})
			}

		} else { //item

		}
	}

	time.Sleep(time.Second)
}
