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

H_PVP_FORMULA = "H_PVP_FORMULA"


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

def calc_pvp_score(card, price_skill_mul):
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
    score += (price * skillRaritySum * price_skill_mul)
    return score


def calc_player_pvp_score(userid, bands, cards, price_skill_mul):
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
                score1 = calc_pvp_score(cards[card_id], price_skill_mul)
            card_id = members[col+colnum]
            if card_id:
                score2 = calc_pvp_score(cards[card_id], price_skill_mul)
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
        price_skill_mul = yield util.redis().hget(H_PVP_FORMULA, "priceSkillMul")
        for card in band:
            if card:
                score = calc_pvp_score(card, price_skill_mul)
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

        price_skill_mul = yield util.redis().hget(H_PVP_FORMULA, "priceSkillMul")
        price_skill_mul = float(price_skill_mul)

        for pvp_band in pvp_bands:
            # calc pvp score
            pvp_score = 0
            username = pvp_band["userName"]
            userid = pvp_band["userId"]
            for card in pvp_band["band"]:
                if card:
                    score = calc_pvp_score(card, price_skill_mul)
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
            # param
            price_skill_mul = float(self.get_argument("priceSkillMul"))
            yield util.redis().hset(H_PVP_FORMULA, "priceSkillMul", price_skill_mul)

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

class GetFormula(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            formula = yield util.redis().hgetall(H_PVP_FORMULA)
            for k, v in formula.iteritems():
                formula[k] = float(v)

            # reply
            reply = util.new_reply()
            reply["formula"] = formula
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


class Match(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # post data
            post_input = json.loads(self.request.body)
            cards = post_input["cards"]
            match_no = post_input["matchNo"]

            price_skill_mul = yield util.redis().hget(H_PVP_FORMULA, "priceSkillMul")
            price_skill_mul = float(price_skill_mul)

            score = 0
            for proto in cards:
                username = card_tbl.get(proto, "name")
                price, hp, atk, dfs, wis, agi, maxlv, skillid1, skillid2= \
                    map(int, card_tbl.gets(proto, "price", \
                    "maxhp", "maxatk", "maxdef", "maxwis", "maxagi", "maxlevel", "skillid1", "skillid2"))

                card = {
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
                }
                
                score += calc_pvp_score(card, price_skill_mul)

            # match
            ## win streak level
            match_level = (match_no-1)/3 + 1
            if match_level < 1 or match_level > 10:
                raise Exception("wrong matchNo: %s" % match_no) 

            ## score level
            score_level = -1
            k = 0
            for k in map(int, pvp_match_tbl.iter_rowkeys()): 
                score_in_tbl = pvp_match_tbl.get(k, "pvpstrength")
                if score < score_in_tbl:
                    score_level = k - 1
                    break
            if score_level == -1:
                score_level = k

            ## pvp foes score range
            colmin = "pvp%dmin" % match_level
            colmax = "pvp%dmax" % match_level
            score_min, score_max = map(int, pvp_match_tbl.gets(score_level, colmin, colmax))
            score_min += score
            score_max += score

            ## get matched rank
            for i in xrange(10):
                pipe = util.redis_pipe()
                pipe.zrevrangebyscore(Z_PVP_BANDS, score_max, score_min, offset = 0, limit=1)
                pipe.zrangebyscore(Z_PVP_BANDS, score_min, score_max, offset = 0, limit=1)
                keyminmax = yield util.redis_pipe_execute(pipe)
                if (not keyminmax[0]) or (not keyminmax[1]) or int(keyminmax[1][0])==int(keyminmax[0][0]):
                    match_level -= 1
                    if match_level == 0:
                        total_rank = yield util.redis().zcard(Z_PVP_BANDS)
                        rankrange = [total_rank-101, total_rank-1]
                        break
                    colmin = "pvp%dmin" % match_level
                    score_min = int(pvp_match_tbl.get(score_level, colmin)) + score
                    continue

                pipe = util.redis_pipe()
                pipe.zrevrank(Z_PVP_BANDS, keyminmax[0][0])
                pipe.zrevrank(Z_PVP_BANDS, keyminmax[1][0])
                rankrange = yield util.redis_pipe_execute(pipe)
                if rankrange[1] - rankrange[0] < 3:
                    match_level -= 1
                    if match_level == 0:
                        total_rank = yield util.redis().zcard(Z_PVP_BANDS)
                        rankrange = [total_rank-101, total_rank-1]
                        break
                    colmin = "pvp%dmin" % match_level
                    score_min = int(pvp_match_tbl.get(score_level, colmin)) + score
                    continue

            # get band
            ranks = random.sample(xrange(rankrange[0], rankrange[1]+1), 3)
            if len(ranks) != 3:
                raise Exception("len(ranks) != 3")
            pipe = util.redis_pipe()
            pipe.zrevrange(Z_PVP_BANDS, ranks[0], ranks[0], True)
            pipe.zrevrange(Z_PVP_BANDS, ranks[1], ranks[1], True)
            pipe.zrevrange(Z_PVP_BANDS, ranks[2], ranks[2], True)
            members = yield util.redis_pipe_execute(pipe)
            # 
            pipe = util.redis_pipe()
            pipe.hget(H_PVP_BANDS, members[0][0][0])
            pipe.hget(H_PVP_BANDS, members[1][0][0])
            pipe.hget(H_PVP_BANDS, members[2][0][0])
            matched_bands = yield util.redis_pipe_execute(pipe)
            matched_bands = [json.loads(band) for band in matched_bands]
            print matched_bands
            
            
            # reply
            reply = util.new_reply()
            reply["score"] = score
            reply["rankrange"] = rankrange
            reply["scorerange"] = [score_min, score_max]
            reply["matchedBands"] = matched_bands
            reply["members"] = members
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
        util.tr().zrevrange(Z_PVP_BANDS, 0, -1, callback=self.onResult)
        
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
            foo = yield adisp.async(util.tr().zrevrange)(Z_PVP_BANDS, 0, -1)
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
            for i in xrange(10):
                foo = yield tornado.gen.Task(util.tr().zrevrange, Z_PVP_BANDS, 0, -1)
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
    (r"/whapi/pvp/getformula", GetFormula),
    (r"/whapi/pvp/match", Match),
    (r"/whapi/pvp/test", Test),
    (r"/whapi/pvp/test1", Test1),
    (r"/whapi/pvp/test2", Test2),
    (r"/whapi/pvp/toredis", Toredis),
    (r"/whapi/pvp/toredisa", ToredisAdisp),
    (r"/whapi/pvp/toredisg", ToredisGen),
]

pvp_match_tbl = util.CsvTbl("data/pvpmatch.csv", "id")
