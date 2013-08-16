from error import *
import util
from session import *
import tornado.web
import adisp
import brukva
import json
import logging
import pickle
import datetime
import time

"""
    "leaderboard_endtime_zsets" => sortedSets{
                                        score:endtime, 
                                        member:leaderboard_key
                                    }

    "leaderboard_infos" =>  hashes{
                                leaderboard_key:{
                                    "begintime":datetime, 
                                    "endtime":datetime, 
                                    "order":string(ASC|DESC)
                                }
                            }

    leaderboard_result_key =>   sortedSets{
                                    score:score, 
                                    member:userid
                                }

    leaderboard_result_info_key =>  hashes{
                                        userid: {
                                            "username":string,
                                            "submittime":datetime,
                                        },
                                    }
"""

def get_leaderbard_result_key(key):
    return "leaderboard_result/"+key

def get_leaderboard_result_info_key(key):
    return "leaderboard_result_info/"+key

@adisp.async
@adisp.process
def create(key, begintime, endtime, order, callback):
    try:
        if order not in ("ASC", "DESC"):
            raise Exception("invalid order")

        # now = datetime.datetime.now()
        # if begintime > now or endtime > now:
        #     raise Exception("begintime > now or endtime > now")

        if begintime >= endtime:
            raise Exception("begintime >= endtime")

        # try add to hash["leaderboard_infos"]
        leaderboard_info = {
            "begintime": begintime, 
            "endtime": endtime,
            "order": order
        }
        ok = yield util.redis().hsetnx("leaderboard_infos", key, pickle.dumps(leaderboard_info))
        if not ok:
            raise Exception("leaderboard exists")

        # add to sortedSets["leaderboard_endtime_zsets"]
        t = time.mktime(endtime.timetuple())
        yield util.redis().zadd("leaderboard_endtime_zsets", t, key)

        callback(None)
    except Exception as e:
        callback(e)
    

@adisp.async
@adisp.process
def delete(key, callback):
    try:
        pipe = util.redis_pipe()
        pipe.hdel("leaderboard_infos", key)
        pipe.zrem("leaderboard_endtime_zsets", key)
        leaderboard_result_key = get_leaderbard_result_key(key)
        leaderboard_result_info_key = get_leaderboard_result_info_key(key)
        pipe.delete(leaderboard_result_key)
        pipe.delete(leaderboard_result_info_key)
        yield util.redis_pipe_execute(pipe)

        callback(None)
    except Exception as e:
        callback(e)


@adisp.async
@adisp.process
def set_score(leaderboard_key, score, userid, username, userinfo, callback):
    try:
        leaderboard_result_key = get_leaderbard_result_key(leaderboard_key)
        leaderboard_result_info_key = get_leaderboard_result_info_key(leaderboard_key)
        score = int(score)

        pipe = util.redis_pipe()
        pipe.zadd(leaderboard_result_key, score, userid)
        info = {}
        info["username"] = username
        info["submittime"] = datetime.datetime.now()
        if userinfo:
            info["userinfo"] = userinfo
        pipe.hset(leaderboard_result_info_key, userid, pickle.dumps(info))
        yield util.redis_pipe_execute(pipe)

        callback(None)
    except Exception as e:
        callback(e)


@adisp.async
@adisp.process
def get_score_and_rank(leaderboard_key, userid, callback):
    try:
        leaderboard_info = yield util.redis().hget("leaderboard_infos", leaderboard_key)
        leaderboard_info = pickle.loads(leaderboard_info)
        order = leaderboard_info["order"]

        pipe = util.redis_pipe()
        leaderboard_result_key = get_leaderbard_result_key(leaderboard_key)
        pipe.zscore(leaderboard_result_key, userid)

        if order == "ASC":
            pipe.zrank(leaderboard_result_key, userid)
        elif order == "DESC":
            pipe.zrevrank(leaderboard_result_key, userid)
        else:
            raise Exception("invalid order")

        score, rank = yield util.redis_pipe_execute(pipe)
        callback((score, rank))
    except Exception as e:
        callback(e)

@adisp.async
@adisp.process
def get_ranks(leaderboard_key, offset, limit, callback):
    try:
        #
        key = leaderboard_key
        offset = max(0, offset)
        limit = max(1, min(30, limit))

        # 
        leaderboard_info = yield util.redis().hget("leaderboard_infos", key)
        leaderboard_info = pickle.loads(leaderboard_info)
        order = leaderboard_info["order"]
        if order == "ASC":
            rangefunc = util.redis().zrange
        elif order == "DESC":
            rangefunc = util.redis().zrevrange
        else:
            raise Exception("invalid order")

        # 
        leaderboard_result_key = get_leaderbard_result_key(key)
        scores = yield rangefunc(leaderboard_result_key, offset, offset+limit, True)

        ranks = []
        userids = [int(s[0]) for s in scores]

        if userids:
            leaderboard_result_info_key = get_leaderboard_result_info_key(key)
            score_infos = yield util.redis().hmget(leaderboard_result_info_key, userids)

            i = offset + 1
            for s in scores:
                rank = {}
                userid, score = int(s[0]), int(s[1])
                info = pickle.loads(score_infos[userid])
                rank["rank"] = i
                rank["userid"] = userid
                rank["username"] = info["username"]
                rank["score"] = score
                rank["submittime"] = util.datetime_to_str(info["submittime"])
                rank["userinfo"] = info["userinfo"]
                ranks.append(rank)
                i += 1

        callback(ranks)
    except Exception as e:
        callback(e)


class Create(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            key = self.get_argument("key")
            begintime = self.get_argument("begintime")
            endtime = self.get_argument("endtime")
            order = self.get_argument("order")

            begintime = util.parse_datetime(begintime)
            endtime = util.parse_datetime(endtime)

            yield create(key, begintime, endtime, order)
            reply = util.new_reply()
            leaderboard = {}
            leaderboard["key"] = key
            leaderboard["begintime"] = util.datetime_to_str(begintime)
            leaderboard["endtime"] = util.datetime_to_str(endtime)
            leaderboard["order"] = order
            reply["leaderboard"] = leaderboard
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class Delete(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            key = self.get_argument("key")

            yield delete(key)
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class List(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            leaderboard_keys = yield util.redis().zrevrange("leaderboard_endtime_zsets", 0, -1, False)
            lbs = yield util.redis().hmget("leaderboard_infos", leaderboard_keys)
            leaderboards = []
            for k in leaderboard_keys:
                l = {}
                v = pickle.loads(lbs[k])
                l["key"] = k
                l["begintime"] = util.datetime_to_str(v["begintime"])
                l["endtime"] = util.datetime_to_str(v["endtime"])
                l["order"] = v["order"]
                leaderboards.append(l)

            reply = util.new_reply()
            reply["leaderboards"] = leaderboards
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class Getranks(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            key = self.get_argument("key")
            offset = int(self.get_argument("offset"))
            limit = int(self.get_argument("limit"))

            ranks = yield get_ranks(key, offset, limit)

            reply = util.new_reply()
            reply["ranks"] = ranks
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class AddScore(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            key = self.get_argument("key")
            score = int(self.get_argument("score"))
            userid = int(self.get_argument("userid"))
            username = self.get_argument("username")

            # 
            yield set_score(key, score, userid, username, None)

            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/leaderboard/create", Create),
    (r"/whapi/leaderboard/delete", Delete),
    (r"/whapi/leaderboard/list", List),
    (r"/whapi/leaderboard/getranks", Getranks),

    (r"/whapi/leaderboard/addscore", AddScore),
]