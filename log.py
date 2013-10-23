from error import *
import util

import tornado.web
import adisp

import json

@adisp.async
@adisp.process
def getEventSerialId(callback):
	newid = yield util.redis().incr("objRunningAutoIncr")
	callback(newid)

type ObjRunningLog struct {
	EventId           uint64
	UserId            uint32
	TypeId            int32
	AddNum            int16
	CurrNumOrEntityId uint64
	EventType         EventType
	Time              int64
}

@adisp.async
@adisp.process
def addObjRunningLog(logs, callback):
	time := util.getRedisTimeUnix()

	pipe = util.redis_pipe()
	for log in logs:
		log["Time"] = time
		jsLog = json.dumps(log)
		pipe.lpush("objRunningAutoIncr")

    yield util.redis_pipe_execute(pipe)
    callback(None)