from session import find_session
from error import *
import util
from card import card_tbl, skill_tbl

import tornado.web, tornado.gen
import adisp

import json
import random
import datetime
import traceback

import redis

""" 
    # pvp score rank, you can find band data from H_PVP_BANDS with user_id
    Redis::SortedSet:
        key: Z_PVP_BANDS
        score: pvp_score
        member: user_id

    # pvp band data
    Redis::Hashe:
        key: H_PVP_BANDS
        field: user_id
        value: {
            "userName":string,
            "score":int,
            "band":{
                "protoId":int,
                "level":int,
                "hp":int,
                "atk":int,
                "def":int,
                "wis":int,
                "agi":int,            
                "skill1Id":int,
                "skill1Level":int,
                "skill2Id":int,
                "skill2Level":int,
                "skill3Id":int,
                "skill3Level":int
            }
        }

    # pvp foes data, remain 10 minutes each
    Redis::String:
        key: S_PVP_FOES,
        value: [
            {
                "userId":int
                "userName":string,
                "score":int,
                "band":{
                    "protoId":int,
                    "level":int,
                    "hp":int,
                    "atk":int,
                    "def":int,
                    "wis":int,
                    "agi":int,
                    "skill1Id":int,
                    "skill1Level":int,
                    "skill2Id":int,
                    "skill2Level":int,
                    "skill3Id":int,
                    "skill3Level":int
            } * 3
        ]
        seconds: 600
"""

PVP_ID_SERIAL = "PVP_ID_SERIAL"
PVP_Z_KEY = "PVP_Z_KEY"
PVP_H_KEY = "PVP_H_KEY"

Z_PVP_BANDS = "Z_PVP_BANDS"
H_PVP_BANDS = "H_PVP_BANDS"
S_PVP_FOES = "S_PVP_FOES"

class AddTestRecord(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            n = 1
            curr_id = yield util.redis().incrby(PVP_ID_SERIAL, n)
            records = []
            pipe = util.redis_pipe()
            for d in xrange(n):
                curr_id += 1
                score = random.random()*10000
                pipe.zadd(PVP_Z_KEY, score, curr_id)
            yield util.redis_pipe_execute(pipe)

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

def calc_pvp_score(card):
    """
        card: {
            "protoId":int,
            "level":int,
            "hp":int,
            "atk":int,
            "def":int,
            "wis":int,
            "agi":int,
            "skill1Id":int,
            "skill1Level":int,
            "skill2Id":int,
            "skill2Level":int,
            "skill3Id":int,
            "skill3Level":int
        }
    """
    card_proto = card_tbl.get_row(card["protoId"])
    price = int(card_tbl.get_value(card_proto, "price"))

    skillRaritySum = 0
    for skillid in [card["skill1Id"], card["skill2Id"], card["skill3Id"]]:
        if skillid:
            skillRaritySum += int(skill_tbl.get(skillid, "rarity"))

    score = card["hp"] + card["atk"] + card["def"] + card["wis"] + card["agi"]
    score += (price * skillRaritySum)
    return score


def calc_player_pvp_score(userid, bands, cards):
    """
        bands: [
            {
                "formation": int,
                "members": [
                    <cardEntityId:int>,
                    ...
                ]
            },
            ...
        ]
        cards: {
            <cardEntityId>: {
                "protoId":int,
                "level":int,
                "hp":int,
                "atk":int,
                "def":int,
                "wis":int,
                "agi":int,
                "skill1Id":int,
                "skill1Level":int,
                "skill2Id":int,
                "skill2Level":int,
                "skill3Id":int,
                "skill3Level":int
            }
        }
    """
    # calc pvp score
    pvp_score = 0
    for band in bands:
        band_score = 0
        formation = int(band["formation"])
        members = band["members"]
        memnum = len(members)
        if (memnum % 2) != 0:
            raise Exception("member number is odd")
        colnum = memnum / 2
        for col in xrange(colnum):
            score1 = score2 = 0
            card_id = members[col]
            if card_id:
                score1 = calc_pvp_score(cards[card_id])
            card_id = members[col+colnum]
            if card_id:
                score2 = calc_pvp_score(cards[card_id])
            band_score += max(score1, score2)
        pvp_score = max(pvp_score, band_score)

    return pvp_score
        

@adisp.async
@adisp.process
def submit_pvp_band(userid, username, band, callback):
    """
        "userId":int
        "userName":string
        "band":[
            {
                "protoId":int,
                "level":int,
                "hp":int,
                "atk":int,
                "def":int,
                "wis":int,
                "agi":int,
                "skill1Id":int,
                "skill1Level":int,
                "skill2Id":int,
                "skill2Level":int,
                "skill3Id":int,
                "skill3Level":int
            },
            ...
        ]
    """
    try:
        # calc pvp score
        pvp_score = 0
        for card in band:
            if card:
                score = calc_pvp_score(card)
                pvp_score += score

        # update to redis
        pipe = util.redis_pipe()
        pipe.zadd(Z_PVP_BANDS, pvp_score, userid)

        pvp_data = {"userName": username, "band":band, "score": pvp_score}
        pipe.hset(H_PVP_BANDS, userid, json.dumps(pvp_data))
        yield util.redis_pipe_execute(pipe)
        
        callback(None)

    except Exception as e:
        traceback.print_exc()
        callback(e)


@adisp.async
@adisp.process
def submit_pvp_bands(pvp_bands, callback):
    """
        pvp_bands:[
            {
                "userId":int,
                "userName":string,
                "band":[
                    {
                        "protoId":int,
                        "level":int,
                        "hp":int,
                        "atk":int,
                        "def":int,
                        "wis":int,
                        "agi":int,
                        "skill1Id":int,
                        "skill1Level":int,
                        "skill2Id":int,
                        "skill2Level":int,
                        "skill3Id":int,
                        "skill3Level":int
                    },
                    ...
                ]
            },
            ...
        ]
    """
    try:
        pipe = util.redis_pipe()

        for pvp_band in pvp_bands:
            # calc pvp score
            pvp_score = 0
            username = pvp_band["userName"]
            userid = pvp_band["userId"]
            for card in pvp_band["band"]:
                if card:
                    score = calc_pvp_score(card)
                    pvp_score += score
            pvp_band["score"] = pvp_score

            # update to redis
            pipe.zadd(Z_PVP_BANDS, pvp_score, userid)
            pipe.hset(H_PVP_BANDS, userid, json.dumps(pvp_band))

        yield util.redis_pipe_execute(pipe)
        callback(None)

    except Exception as e:
        traceback.print_exc()
        callback(e)


@adisp.async
@adisp.process
def get_3_bands(userid, pvpscore, winnum, callback):
    try:
        win_level = int(winnum/3)


    except Exception as e:
        callback(e)


###########################
class CreateTestData(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            bands = []
            for card_row_key in card_tbl.iter_rowkeys():
                username = card_tbl.get(card_row_key, "name")
                proto, price, hp, atk, dfs, wis, agi, maxlv, skillid1, skillid2= \
                    map(int, card_tbl.gets(card_row_key, "ID", "price", \
                    "maxhp", "maxatk", "maxdef", "maxwis", "maxagi", "maxlevel", "skillid1", "skillid2"))

                band = [{
                    "protoId": proto,
                    "level":maxlv,
                    "hp":hp,
                    "atk":atk,
                    "def":dfs,
                    "wis":wis,
                    "agi":agi,
                    "skill1Id":skillid1,
                    "skill1Level":20,
                    "skill2Id":skillid2,
                    "skill2Level":20,
                    "skill3Id":0,
                    "skill3Level":0
                }] * 5
                userid = proto
                pvp_band = {
                    "userId": proto,
                    "userName": username,
                    "band": band
                }

                bands.append(pvp_band)

            yield submit_pvp_bands(bands)

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class Get3Band(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # get player pvp score
            rows = yield util.whdb.runQuery(
                """SELECT pvpScore, bands FROM playerInfos WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            pvp_score = row[0]
            bands = json.loads(row[1])
            members = set()
            for band in bands:
                for mem in band["members"]:
                    if mem:
                        members.add(mem)
            members = tuple(members)
            
            # 
            if pvp_score == 0:
                cols = ["id", "protoId", "level", "hp", "atk", "def", "wis", "agi", \
                    "hpCrystal", "atkCrystal", "defCrystal", "wisCrystal", "agiCrystal", \
                    "hpExtra", "atkExtra", "defExtra", "wisExtra", "agiExtra", \
                    "skill1Id", "skill1Level", "skill2Id", "skill2Level", "skill3Id", "skill3Level"
                ]
                rows = yield util.whdb.runQuery(
                    """SELECT {} FROM cardEntities WHERE ownerId=%s and id IN ({})""".format(",".join(cols), ",".join(map(str, members)))
                    ,(userid, )
                )
                cards = {}
                for row in rows:
                    card = dict(zip(cols, row))
                    card["hp"] += card["hpCrystal"] + card["hpExtra"]
                    card["atk"] += card["atkCrystal"] + card["atkExtra"]
                    card["def"] += card["defCrystal"] + card["defExtra"]
                    card["wis"] += card["wisCrystal"] + card["wisExtra"]
                    card["agi"] += card["agiCrystal"] + card["agiExtra"]
                    cards[card["id"]] = card
                score = calc_player_pvp_score(userid, bands, cards)

            # reply
            reply = util.new_reply()
            reply["score"] = score
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class GetRanks(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    # @adisp.process
    def get(self):
        try:
            r = redis.StrictRedis(host='localhost', port=6379, db=0)
            ranks = r.zrevrange(Z_PVP_BANDS, 0, -1, withscores=True)
            ranks = [{"id":rank[0], "score": rank[1]} for rank in ranks]

            for idx, rank in enumerate(ranks):
                name, maxhp, maxdef, maxatk, maxwis, maxagi, price = \
                    card_tbl.gets(rank["id"], "name", "maxhp", "maxatk", "maxdef", "maxwis", "maxagi", "price")
                rank["index"] = idx
                rank["name"] = name
                rank["maxhp"] = int(maxhp)
                rank["maxdef"] = int(maxdef)
                rank["maxatk"] = int(maxatk)
                rank["maxwis"] = int(maxwis)
                rank["maxagi"] = int(maxagi)
                rank["price"] = int(price)

            # reply
            reply = util.new_reply()
            reply["ranks"] = ranks
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Test(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            foo = yield util.ar.exe("zrevrange", Z_PVP_BANDS, 0, -1)
            # foo = yield util.ar.exe("get", "foo")

            # reply
            reply = util.new_reply()
            reply["foo"] = foo
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Test1(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            foo = yield util.redis().zrevrange(Z_PVP_BANDS, 0, -1, False)
            # foo = yield util.ar.exe("get", "foo")

            # reply
            reply = util.new_reply()
            reply["foo"] = foo
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

import redis
class Test2(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        try:
            r = redis.StrictRedis(host='localhost', port=6379, db=0)
            foo = r.zrevrange(Z_PVP_BANDS, 0, -1)

            # reply
            reply = util.new_reply()
            reply["foo"] = foo
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        
import toredis
class Toredis(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        util.tr.zrevrange(Z_PVP_BANDS, 0, -1, callback=self.onResult)
        
    def onResult(self, result):
        # reply
        reply = util.new_reply()
        reply["result"] = result
        self.write(json.dumps(reply))

        self.finish()

class ToredisAdisp(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            foo = yield adisp.async(util.tr.zrevrange)(Z_PVP_BANDS, 0, -1)
            reply = util.new_reply()
            reply["foo"] = foo
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class ToredisGen(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self):
        try:
            foo = yield tornado.gen.Task(util.tr.zrevrange, Z_PVP_BANDS, 0, -1)
            reply = util.new_reply()
            reply["foo"] = foo
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/pvp/addtestrecord", AddTestRecord),
    (r"/whapi/pvp/createtestdata", CreateTestData),
    (r"/whapi/pvp/get3band", Get3Band),
    (r"/whapi/pvp/getranks", GetRanks),
    (r"/whapi/pvp/test", Test),
    (r"/whapi/pvp/test1", Test1),
    (r"/whapi/pvp/test2", Test2),
    (r"/whapi/pvp/toredis", Toredis),
    (r"/whapi/pvp/toredisa", ToredisAdisp),
    (r"/whapi/pvp/toredisg", ToredisGen),
]
