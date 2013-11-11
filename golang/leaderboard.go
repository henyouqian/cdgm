package main

import (
	"encoding/json"
	"github.com/garyburd/redigo/redis"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
)

type Order string

const (
	ORDER_ASC  = Order("ASC")
	ORDER_DESC = Order("DESC")
)

func makeLBResultKey(lbname string) string {
	return "leaderboard_result/" + lbname
}

func makeLBResultPlayerKey(lbname string) string {
	return "leaderboard_result_info/" + lbname
}

func GetScoreAndRank(rc redis.Conn, lbname string, userid uint32, order Order) (score, rank uint32, err error) {
	key := makeLBResultKey(lbname)

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
	rank = uint32(_rank) + 1
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

func ClearLeaderboard(rc redis.Conn, lbname string) error {
	key0 := makeLBResultKey(lbname)
	key1 := makeLBResultPlayerKey(lbname)

	_, err := rc.Do("del", key0, key1)
	return lwutil.NewErr(err)

	//glog.Info("ClearLeaderboard")
	return nil
}

func leaderboardSendRewards(rc redis.Conn, lbname string) error {
	var rewardCsv []rowReward
	var order Order
	switch lbname {
	case "pvp":
		rewardCsv = tblPvpRankRewardsList
		order = ORDER_DESC
	}
	if len(rewardCsv) == 0 {
		return lwutil.NewErrStr("reward csv not found: lbname=" + lbname)
	}

	if order != ORDER_DESC && order != ORDER_ASC {
		return lwutil.NewErrStr("invalid order: lbname=" + lbname)
	}

	//get max rank from csv
	maxRank := uint32(0)
	for _, v := range rewardCsv {
		if v.RankTo > maxRank {
			maxRank = v.RankTo
		}
	}

	//
	keyRes := makeLBResultKey(lbname)

	if order == ORDER_ASC {
		rc.Send("zrange", keyRes, 0, maxRank-1)
	} else if order == ORDER_DESC {
		rc.Send("zrevrange", keyRes, 0, maxRank-1)
	}
	rc.Flush()
	playerIdValues, err := redis.Values(rc.Receive())
	if err != nil {
		return lwutil.NewErr(err)
	}

	//fixme: for test
	testData := []interface{}{int64(24), int64(3663), int64(4), int64(5), int64(23), int64(64), int64(255), int64(567)}
	playerIdValues = testData

	rewardRowIdx := 0
	rewardRowNum := len(rewardCsv)
	for rankIdx, userIdRaw := range playerIdValues {
		_userId, err := redis.Int(userIdRaw, nil)
		if err != nil {
			return lwutil.NewErr(err)
		}
		userId := uint32(_userId)

		rank := uint32(rankIdx + 1)
		for i := rewardRowIdx; i < rewardRowNum; i++ {
			rewardRow := rewardCsv[i]
			if rank >= rewardRow.RankFrom && rank <= rewardRow.RankTo {
				rewards := make([]Reward, 0, 3)
				if rewardRow.Reward1 != 0 {
					reward1 := Reward{
						rewardRow.Reward1,
						rewardRow.Amount1,
						userId,
						STR_PVP_REWARD,
					}
					rewards = append(rewards, reward1)
				}

				if rewardRow.Reward2 != 0 {
					reward2 := Reward{
						rewardRow.Reward2,
						rewardRow.Amount2,
						userId,
						STR_PVP_REWARD,
					}
					rewards = append(rewards, reward2)
				}

				if rewardRow.Reward3 != 0 {
					reward3 := Reward{
						rewardRow.Reward3,
						rewardRow.Amount3,
						userId,
						STR_PVP_REWARD,
					}
					rewards = append(rewards, reward3)
				}

				//add cards and items
				protoAndLvs := make([]cardProtoAndLevel, 0, 8)
				items := make([]ItemInfo, 0, 8)
				for _, rew := range rewards {
					if rew.ObjId < 0 { //card
						cardProto := uint32(-rew.ObjId)
						for i := uint32(0); i < rew.Num; i++ {
							protoAndLvs = append(protoAndLvs, cardProtoAndLevel{cardProto, 1})
						}
					} else { //item
						items = append(items, ItemInfo{uint32(rew.ObjId), rew.Num})
					}
				}
				if len(protoAndLvs) > 0 {
					glog.Infoln("createCards", protoAndLvs)
					//_, err := createCards(userId, protoAndLvs, 0, WAGON_INDEX_GENERAL, STR_PVP_REWARD)
					//if err != nil {
					//	return lwutil.NewErr(err)
					//}
				}
				if len(items) > 0 {
					glog.Infoln("wagonAddItems", items)
					//err := wagonAddItems(WAGON_INDEX_GENERAL, userId, items, STR_PVP_REWARD)
					//if err != nil {
					//	return lwutil.NewErr(err)
					//}
				}

				rewardRowIdx = i
				break
			}
		}
	}

	return nil
}

//below are use new format in redis

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

func LeaderboardGetScoreAndRank(rc redis.Conn, lbname string, userId uint32) (score uint32, rank uint32, err error) {
	infoKey := leaderboardInfoKey(lbname)
	jsInfo, err := redis.Bytes(rc.Do("get", infoKey))
	if err != nil {
		return 0, 0, lwutil.NewErr(err)
	}
	var info LeaderboardInfo
	err = json.Unmarshal(jsInfo, &info)
	if err != nil {
		return 0, 0, lwutil.NewErr(err)
	}

	resultKey := leaderboardResultKey(lbname)
	rc.Send("zscore", resultKey, userId)

	switch info.Order {
	case ORDER_ASC:
		rc.Send("zrank", resultKey, userId)
	}
	if info.Order == ORDER_ASC {
		rc.Send("zrevrank", resultKey, userId)
	}

	err = rc.Flush()
	if err != nil {
		return 0, 0, lwutil.NewErr(err)
	}

	_score, err := redis.Int(rc.Receive())
	if err != nil {
		return 0, 0, lwutil.NewErr(err)
	}
	_rank, err := redis.Int(rc.Receive())
	if err != nil {
		return 0, 0, lwutil.NewErr(err)
	}

	return uint32(_score), uint32(_rank), lwutil.NewErr(err)
}
