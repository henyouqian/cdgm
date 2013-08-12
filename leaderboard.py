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
    "leaderboard_endtime_zsets" => sortedSets{score:endtime, member:leaderboard_name}
    "leaderboard_infos" => hashes{leaderboard_name:{"begintime":datetime, "endtime":datetime, 
                                    "leaderboard_result_key":string, "order":string(ASC|DESC)}}
    leaderboard_result_key => sortedSets{score:score, member:userid}
"""

@adisp.async
@adisp.process
def create(name, begintime, endtime, order, callback):
    try:
        if order not in ("ASC", "DESC"):
            raise Exception("invalid order")

        now = datetime.datetime.now()
        if begintime > now or endtime > now:
            raise Exception("begintime > now or endtime > now")

        print begintime, endtime
        if begintime >= endtime:
            raise Exception("begintime >= endtime")

        # try add to hash["leaderboard_infos"]
        leaderboard_result_key = "leaderboard_result/"+name
        leaderboard_info = {
            "begintime": begintime, 
            "endtime": endtime,
            "leaderboard_result_key": leaderboard_result_key,
            "order": order
        }
        ok = yield util.redis().hsetnx("leaderboard_infos", name, pickle.dumps(leaderboard_info))
        if not ok:
            raise Exception("leaderboard exists")

        # add to sortedSets["leaderboard_endtime_zsets"]
        t = time.mktime(endtime.timetuple())
        yield util.redis().zadd("leaderboard_endtime_zsets", t, name)

        callback(None)
    except Exception as e:
        callback(e)
    

@adisp.async
@adisp.process
def delete(name, callback):
    try:
        pipe = util.redis_pipe()
        pipe.hdel("leaderboard_infos", name)
        pipe.zrem("leaderboard_endtime_zsets", name)
        leaderboard_result_key = "leaderboard_result/"+name
        pipe.delete(leaderboard_result_key)
        yield util.redis_pipe_execute(pipe)

        callback(None)
    except Exception as e:
        callback(e)


@adisp.async
@adisp.process
def add_score(leaderboard_result_key, score):
    try:
        yield util.redis().zadd(leaderboard_result_key, score, userid)
        callback(None)
    except Exception as e:
        callback(e)


class Create(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            name = self.get_argument("name")
            begintime = self.get_argument("begintime")
            endtime = self.get_argument("endtime")
            order = self.get_argument("order")

            begintime = util.parse_datetime(begintime)
            endtime = util.parse_datetime(endtime)

            yield create(name, begintime, endtime, order)
            reply = util.new_reply()
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
            name = self.get_argument("name")

            yield delete(name)
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
            leaderboard_names = yield util.redis().zrange("leaderboard_endtime_zsets", 0, -1, False)
            lbs = yield util.redis().hmget("leaderboard_infos", leaderboard_names)
            leaderboards = []
            for k, v in lbs.iteritems():
                l = {}
                v = pickle.loads(v)
                l["name"] = k
                l["begintime"] = util.datetime_to_str(v["begintime"])
                l["endtime"] = util.datetime_to_str(v["endtime"])
                del l["leaderboard_result_key"]
                leaderboards.append(l)

            reply = util.new_reply()
            reply["leaderboards"] = leaderboards
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


handlers = [
    (r"/whapi/leaderboard/create", Create),
    (r"/whapi/leaderboard/delete", Delete),
    (r"/whapi/leaderboard/list", List),
]