package main

import (
	"encoding/json"
	"github.com/garyburd/redigo/redis"
	"github.com/henyouqian/lwutil"
)

type EventType uint8

const (
	EVT_ADV_CASE EventType = iota
	EVT_WOOD_CASE
	EVT_MAP_GEN
	EVT_MON_DROP
	EVT_MISSION_REWARD
	EVT_SYS_OFFER
	EVT_ADMIN
	EVT_EVENT_REWARD
	EVT_PVP_REWARD
	EVT_CAMPAIGN
	EVT_RECHARGE
	EVT_USE
	EVT_EMPOWER
	EVT_ENTER_INSTANCE
	EVT_SACRIFICE
	EVT_GET_CARD_LOW
	EVT_GET_CARD_MID
	EVT_GET_CARD_HI
	EVT_GET_CARD_DIAMOND
	EVT_EVOLUTION
	EVT_SHOPPING
)

type ObjRunningLog struct {
	EventId           uint64
	UserId            uint32
	TypeId            int32
	AddNum            int16
	CurrNumOrEntityId uint64
	EventType         EventType
	Time              int64
}

func addObjRunningLog(logs []ObjRunningLog) error {
	time := lwutil.GetRedisTimeUnix()

	rc := redisPool.Get()
	defer rc.Close()

	jsArgs := make([]interface{}, len(logs)+1)
	jsArgs[0] = "objRunning"
	for i, v := range logs {
		logs[i].Time = time
		jsEntity, err := json.Marshal(&v)
		if err != nil {
			return err
		}
		jsArgs = append(jsArgs, jsEntity)
	}

	_, err := rc.Do("lpush", jsArgs...)
	if err != nil {
		return err
	}

	return nil
}

func createCardRunning(eventId uint64, userId uint32, protoId uint32, entityId uint64, addNum int16, eventType EventType) *ObjRunningLog {
	return &ObjRunningLog{
		eventId, userId, int32(protoId), addNum, entityId, eventType, 0,
	}
}

func createItemRunning(eventId uint64, userId uint32, itemId uint32, addNum int16, currNum uint32, eventType EventType) *ObjRunningLog {
	return &ObjRunningLog{
		eventId, userId, -int32(itemId), addNum, uint64(currNum), eventType, 0,
	}
}

func getEventSerialId() (uint64, error) {
	rc := redisPool.Get()
	defer rc.Close()

	id, err := redis.Int64(rc.Do("incr", "objRunningAutoIncr"))
	return uint64(id), err
}

func saveObjRunningToDb() {

}
