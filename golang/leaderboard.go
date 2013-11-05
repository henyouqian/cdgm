package main

import (
	"github.com/garyburd/redigo/redis"
	"github.com/henyouqian/lwutil"
)

type Order string

const (
	ORDER_ASC  = Order("ASC")
	ORDER_DESC = Order("DESC")
)

func makeLeaderboardKey(in string) string {
	return "leaderboard_result/" + in
}

func GetScoreAndRank(key string, userid uint32, order Order) (score, rank uint32, err error) {
	rc := redisPool.Get()
	defer rc.Close()

	key = makeLeaderboardKey(key)

	rc.Send("zscore", key, userid)

	switch order {
	case ORDER_ASC:
		rc.Send("zrank", key, userid)
	case ORDER_DESC:
		rc.Send("zrevrank", key, userid)
	default:
		err = lwutil.NewErrStr("invalid order")
		return
	}

	rc.Flush()

	_score, err := redis.Int(rc.Receive())
	score = uint32(_score)
	if err == redis.ErrNil {
		score = 0
		rank = 0
		err = nil
		return
	}
	if err != nil {
		return
	}

	_rank, err := redis.Int(rc.Receive())
	rank = uint32(_rank)
	if err == redis.ErrNil {
		score = 0
		rank = 0
		err = nil
		return
	}
	if err != nil {
		return
	}

	return
}
