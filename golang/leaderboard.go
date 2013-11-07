package main

import (
	"encoding/json"
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

type LeaderboardInfo struct {
	Name       string
	Order      Order
	RewardsCsv string
	BeginTime  int64
	EndTime    int64
}

type LeaderboardPlayerInfo struct {
	Id          uint32
	Name        string
	SubmmitTime int64
	WarlordLv   uint32
	cardProtos  []uint32
}

func leaderboardInfoKey(lbname string) string {
	return "leaderboardInfo/" + lbname
}

func leaderboardResultKey(lbname string) string {
	return "leaderboardResult/" + lbname
}

func leaderboardPlayerKey(lbname string) string {
	return "leaderboardPlayer/" + lbname
}

func LeaderboardCreate(rc redis.Conn, info *LeaderboardInfo) error {
	key := leaderboardInfoKey(info.Name)
	js, err := json.Marshal(info)
	if err != nil {
		return lwutil.NewErr(err)
	}

	_, err = rc.Do("set", key, js)
	return lwutil.NewErr(err)
}

func LeaderboardDelete(rc redis.Conn, lbname string) error {
	_, err := rc.Do("del", leaderboardInfoKey(lbname), leaderboardResultKey(lbname), leaderboardPlayerKey(lbname))
	return lwutil.NewErr(err)
}

func LeaderboardReset(rc redis.Conn, lbname string) error {
	_, err := rc.Do("del", leaderboardResultKey(lbname), leaderboardPlayerKey(lbname))
	return lwutil.NewErr(err)
}

func LeaderboardSetScore(rc redis.Conn, lbname string, userId uint32, score uint32,
	userName string, warlordLv uint32, cardProtos []uint32) error {

	playerInfo := LeaderboardPlayerInfo{
		userId, userName, lwutil.GetRedisTimeUnix(), warlordLv, cardProtos,
	}
	jsPlayerInfo, err := json.Marshal(playerInfo)
	if err != nil {
		return lwutil.NewErr(err)
	}
	playerKey := leaderboardPlayerKey(lbname)
	rc.Send("hset", playerKey, userId, jsPlayerInfo)

	resultKey := leaderboardResultKey(lbname)
	_, err = rc.Do("zadd", resultKey, score, userId)

	return lwutil.NewErr(err)
}

func LeaderboardScoreAndRank(rc redis.Conn, lbname string, userId uint32) (score uint32, rank uint32, err error) {
	resultKey := leaderboardResultKey(lbname)
	rc.Send("zscore", resultKey, userId)
	
	if order == "ASC":
        pipe.zrank(leaderboard_result_key, userid)
    elif order == "DESC":
        pipe.zrevrank(leaderboard_result_key, userid)
    else:
        raise Exception("invalid order")

	return
}
