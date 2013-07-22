from session import find_session
from error import *
import util
from card import card_tbl, skill_tbl, is_war_lord, warlord_level_tbl, card_level_tbl, calc_card_proto_attr
from gamedata import XP_ADD_DURATION

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
            "userLevel":int,
            "score":int,
            "cards":[
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
                }
            ]
        }

    # pvp foes data, remain 10 minutes each
    Redis::String:
        key: S_PVP_FOES,
        value: [
            {
                "userId":int
                "userName":string,
                "score":int,
                "card":{
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
def update_pvp_band(userid, username, userlevel, bands, callback):
    """
        "userId":int
        "userName":string
        "bands":[
            {
                "formation": {INT}, 
                "cards": [
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
            }
            ...
        ]
    """
    try:
        # calc pvp score
        pvp_score = 0
        price_skill_mul = yield util.redis().hget(H_PVP_FORMULA, "priceSkillMul")
        price_skill_mul = float(price_skill_mul)

        max_band_score = 0
        max_score_band = None
        for band in bands:
            # calc pvp score
            band_score = 0
            cards = band["cards"]
            cardnum = len(cards)
            if (cardnum % 2) != 0:
                raise Exception("card number is odd")
            colnum = cardnum / 2

            better_cards = []
            for col in xrange(colnum):
                score1 = score2 = 0
                card1 = cards[col]
                if card1:
                    score1 = calc_pvp_score(card1, price_skill_mul)
                card2 = cards[col+colnum]
                if card2:
                    score2 = calc_pvp_score(card2, price_skill_mul)

                if (score2 > score1):
                    band_score += score2
                    better_cards.append(card2)
                else:
                    band_score += score1
                    better_cards.append(card1)

            if band_score > max_band_score:
                max_band_score = band_score
                max_score_band = {}
                max_score_band["formation"] = band["formation"]
                max_score_band["cards"] = better_cards
                max_score_band["userId"] = userid
                max_score_band["userName"] = username
                max_score_band["userLevel"] = userlevel
                max_score_band["score"] = max_band_score
                

        # update to redis
        pipe = util.redis_pipe()
        print json.dumps(max_score_band)
        pipe.zadd(Z_PVP_BANDS, max_band_score, userid)
        pipe.hset(H_PVP_BANDS, userid, json.dumps(max_score_band))
        yield util.redis_pipe_execute(pipe)
        
        callback(max_band_score)

    except Exception as e:
        traceback.print_exc()
        callback(e)


# @adisp.async
# @adisp.process
# def submit_pvp_band(userid, username, cards, callback):
#     """
#         "userId":int
#         "userName":string
#         "cards":[
#             {
#                 "protoId":int,
#                 "level":int,
#                 "hp":int,
#                 "atk":int,
#                 "def":int,
#                 "wis":int,
#                 "agi":int,
#                 "skill1Id":int,
#                 "skill1Level":int,
#                 "skill2Id":int,
#                 "skill2Level":int,
#                 "skill3Id":int,
#                 "skill3Level":int
#             },
#             ...
#         ]
#     """
#     try:
#         # calc pvp score
#         pvp_score = 0
#         price_skill_mul = yield util.redis().hget(H_PVP_FORMULA, "priceSkillMul")
#         price_skill_mul = float(price_skill_mul)
#         for card in cards:
#             if card:
#                 score = calc_pvp_score(card, price_skill_mul)
#                 pvp_score += score

#         # update to redis
#         pipe = util.redis_pipe()
#         pipe.zadd(Z_PVP_BANDS, pvp_score, userid)

#         pvp_data = {"userName": username, "cards":cards, "score": pvp_score}
#         pipe.hset(H_PVP_BANDS, userid, json.dumps(pvp_data))
#         yield util.redis_pipe_execute(pipe)
        
#         callback(None)

#     except Exception as e:
#         traceback.print_exc()
#         callback(e)


@adisp.async
@adisp.process
def submit_pvp_bands(pvp_bands, callback):
    """
        pvp_bands:[
            {
                "userId":int,
                "userName":string,
                "formation":int,
                "cards":[
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
            for card in pvp_band["cards"]:
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


###########################
class CreateTestData(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            price_skill_mul = float(self.get_argument("priceSkillMul"))
            yield util.redis().hset(H_PVP_FORMULA, "priceSkillMul", price_skill_mul)

            # clear all
            pipe = util.redis_pipe()
            pipe.delete(Z_PVP_BANDS)
            pipe.delete(H_PVP_BANDS)
            pipe.delete(S_PVP_FOES)
            yield util.redis_pipe_execute(pipe)


            # same five member
            bands = []
            for card_row_key in card_tbl.iter_rowkeys():
                username = card_tbl.get(card_row_key, "name")
                proto, price, hp, atk, dfs, wis, agi, maxlv, skillid1, skillid2= \
                    map(int, card_tbl.gets(card_row_key, "ID", "price", \
                    "maxhp", "maxatk", "maxdef", "maxwis", "maxagi", "maxlevel", "skillid1", "skillid2"))

                cards = [{
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

                pvp_band = {
                    "userId": -proto,
                    "userName": username,
                    "userLevel": 1,
                    "cards": cards,
                    "formation":14,
                }

                bands.append(pvp_band)

            # yield submit_pvp_bands(bands)

            # parse pvp test data
            test_data = {}
            for key in pvp_test_data_tbl.iter_rowkeys():
                tp, proto = map(int, pvp_test_data_tbl.gets(key, "type", "ID"))
                rarity = int(card_tbl.get(proto, "rarity"))
                if tp == 0:
                    for i in xrange(1, 4):
                        k = (i, rarity)
                        if not test_data.get(k, None):
                            test_data[k] = []
                        test_data[k].append(int(key))
                else:
                    k = (tp, rarity)
                    if not test_data.get(k, None):
                        test_data[k] = []
                    test_data[k].append(int(key))


            # add type=1, rarity=1
            yield self.batchAdd(test_data, 1, 1, 2000)
            yield self.batchAdd(test_data, 1, 2, 2000)
            yield self.batchAdd(test_data, 1, 3, 2000)
            yield self.batchAdd(test_data, 1, 4, 2000)
            # yield self.batchAdd(test_data, 1, 5, 1000)

            yield self.batchAdd(test_data, 2, 1, 2000)
            yield self.batchAdd(test_data, 2, 2, 2000)
            yield self.batchAdd(test_data, 2, 3, 2000)
            yield self.batchAdd(test_data, 2, 4, 2000)
            # yield self.batchAdd(test_data, 2, 5, 1000)

            yield self.batchAdd(test_data, 3, 1, 2000)
            yield self.batchAdd(test_data, 3, 2, 2000)
            yield self.batchAdd(test_data, 3, 3, 2000)
            yield self.batchAdd(test_data, 3, 4, 2000)
            # yield self.batchAdd(test_data, 3, 5, 1000)

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

    @adisp.async
    @adisp.process
    def batchAdd(self, test_data, type, rarity, count, callback):
        try:
            # type = 1, rarity = 1
            key = (type, rarity)
            card_ids = test_data[key]
            bands = []
            
            for i_band in xrange(count):
                member_num = random.randint(3, 5)
                member_protos = random.sample(card_ids, min(member_num, len(card_ids)))
                cards = []
                formation_dict = {3:(1, 4), 4:(5, 10), 5:(11, 19)}
                formation_range = formation_dict[member_num]
                formation = random.randint(formation_range[0], formation_range[1])
                for member_proto in member_protos:
                    price, maxlv, skillid1, skillid2= \
                        map(int, card_tbl.gets(member_proto, "price", \
                            "maxlevel", "skillid1", "skillid2"))
                    level = random.randint(1, maxlv)
                    hp, atk, dfs, wis, agi = calc_card_proto_attr(member_proto, level)
                    cards.append({
                        "protoId": member_proto,
                        "level":level,
                        "hp":hp,
                        "atk":atk,
                        "def":dfs,
                        "wis":wis,
                        "agi":agi,
                        "skill1Id":skillid1,
                        "skill1Level":random.randint(5, 20),
                        "skill2Id":skillid2,
                        "skill2Level":random.randint(5, 20),
                        "skill3Id":0,
                        "skill3Level":0
                    })


                pvp_band = {
                    "userId": -((key[0]*10+key[1])*1000000+i_band),
                    "userName": "%s, %s, %s" %(key[0], key[1], i_band),
                    "userLevel": 1,
                    "cards": cards,
                    "formation":formation,
                }
                bands.append(pvp_band)

            yield submit_pvp_bands(bands)
            callback(None)

        except Exception as e:
            traceback.print_exc()
            callback(e)


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
    @adisp.process
    def get(self):
        try:
            # param
            offset = int(self.get_argument("offset"))
            limit = int(self.get_argument("limit"))

            # 
            r = redis.StrictRedis(host='localhost', port=6379, db=0)
            ranks = r.zrevrange(Z_PVP_BANDS, offset, offset+limit-1, withscores=True)
            ranks = [{"id":int(rank[0]), "score": rank[1]} for rank in ranks]

            pipe = util.redis_pipe()
            for rank in ranks:
                pipe.hget(H_PVP_BANDS, rank["id"])
            bands = yield util.redis_pipe_execute(pipe)

            for i, band in enumerate(bands):
                bands[i] = json.loads(band)

            bands = {band["userId"]:band for band in bands}

            out_ranks = []
            for idx, rank in enumerate(ranks):
                # name, maxhp, maxdef, maxatk, maxwis, maxagi, price = \
                #     card_tbl.gets(rank["id"], "name", "maxhp", "maxatk", "maxdef", "maxwis", "maxagi", "price")
                band = bands[rank["id"]]
                band["index"] = idx+offset
                out_ranks.append(band)

            # reply
            reply = util.new_reply()
            reply["ranks"] = out_ranks
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()


@adisp.async
@adisp.process
def match(score, match_no, user_id, callback):
    try:
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

        BAND_NUM = 4

        ## get matched rank
        for i in xrange(10):
            pipe = util.redis_pipe()
            pipe.zrevrangebyscore(Z_PVP_BANDS, score_max, score_min, offset = 0, limit=1)
            pipe.zrangebyscore(Z_PVP_BANDS, score_min, score_max, offset = 0, limit=1)
            keyminmax = yield util.redis_pipe_execute(pipe)
            print "kkkkkkkkkk", keyminmax
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
            if rankrange[1] - rankrange[0] < BAND_NUM:
                match_level -= 1
                if match_level == 0:
                    total_rank = yield util.redis().zcard(Z_PVP_BANDS)
                    rankrange = [total_rank-101, total_rank-1]
                    break
                colmin = "pvp%dmin" % match_level
                score_min = int(pvp_match_tbl.get(score_level, colmin)) + score
                continue

        # get band
        ranks = random.sample(xrange(rankrange[0], rankrange[1]+1), BAND_NUM)
        if len(ranks) != BAND_NUM:
            raise Exception("len(ranks) != %s" % BAND_NUM)

        pipe = util.redis_pipe()
        for i in xrange(BAND_NUM):
            pipe.zrevrange(Z_PVP_BANDS, ranks[i], ranks[i], True)
        members = yield util.redis_pipe_execute(pipe)
        # 
        pipe = util.redis_pipe()
        for i in xrange(BAND_NUM):
            pipe.hget(H_PVP_BANDS, members[i][0][0])
        matched_bands = yield util.redis_pipe_execute(pipe)

        bands = []
        for band in matched_bands:
            band = json.loads(band)
            if band["userId"] != user_id:
                bands.append(band)
        matched_bands = bands[:3]

        callback((matched_bands, rankrange, score_min, score_max))

    except Exception as e:
        traceback.print_exc()
        callback(e)


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
            matched_bands, rankrange, score_min, score_max = yield match(score, match_no, 0)

            for band in matched_bands:
                for i, card in enumerate(band["cards"]):
                    band["cards"][i] = card_tbl.get(card["protoId"], "name")
                    # card["name"] = card_tbl.get(card["protoId"], "name")
                    card.clear()
                    # card = {"name":card_tbl.get(card["protoId"], "name"), ""]

            # reply
            reply = util.new_reply()
            reply["score"] = score
            reply["rankrange"] = rankrange
            reply["scorerange"] = [score_min, score_max]
            reply["matchedBands"] = matched_bands
            # reply["members"] = members
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()


class BattleResult(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # post data
            post_input = json.loads(self.request.body)
            is_win = post_input["isWin"]
            foe_user_id = post_input["foeUserId"]
            members = post_input["members"]
            allout = post_input["allout"]
            use_item = post_input["useItem"]
            band_index = post_input["bandIndex"]

            # get player info
            rows = yield util.whdb.runQuery(
                """ SELECT items, maxCardNum, ap, maxAp, xp, maxXp, lastXpTime, UTC_TIMESTAMP(), \
                    bands, maxBandNum, warLord, zoneCache, pvpWinStreak, pvpScore FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            items = json.loads(row[0])
            items = {int(k):v for k, v in items.iteritems()}
            max_card_num = row[1]
            ap = row[2]
            max_ap = row[3]
            xp = row[4]
            max_xp = row[5]
            last_xp_time = row[6]
            curr_time = row[7]
            bands = json.loads(row[8])
            max_band_num = row[9]
            warlord = row[10]
            zone_cache = row[11]
            zone_cache = json.loads(zone_cache)
            win_streak = row[12]
            pvp_score = row[13]

            # validate band members
            if band_index not in xrange(max_band_num) or band_index >= len(bands):
                raise Exception("wrong bandIndex: %s" % band_index)
            self_band = bands[band_index]

            members = [member for member in members if member]

            if len(members) == 0:
                raise Exception("no members")
            if len(members) != len(set(members)):
                raise Exception("members repeated")

            for member in members:
                if member not in self_band["members"]:
                    raise Exception("member not in band: %s" % member)

            # get matched bands
            key = "pvpFoeBands/%s" % userid
            matched_bands = yield util.redis().get(key)
            if matched_bands:
                matched_bands = json.loads(matched_bands)
            else:
                send_error(self, "err_timeout")
                return

            foe_band = None
            for mb in matched_bands:
                if mb["userId"] == foe_user_id:
                    foe_band = mb
                    break

            if not foe_band:
                print matched_bands
                raise Exception("foe band not found: foe userId = %s" % foe_user_id)

            # refresh xp
            if not last_xp_time:
                last_xp_time = datetime(2013, 1, 1)

            dt = curr_time - last_xp_time
            dt = int(dt.total_seconds())
            dxp = dt // XP_ADD_DURATION
            if dxp:
                xp = min(max_xp, xp + dxp)
            if xp == max_xp:
                last_xp_time = curr_time
            else:
                last_xp_time = curr_time - datetime.timedelta(seconds = dt % XP_ADD_DURATION)
            dt = curr_time - last_xp_time
            nextAddXpTime = int(dt.total_seconds())

            # comsume xp
            consumeXp = 3 if allout else 1
            if consumeXp > xp:
                if use_item == 1:
                    resumeItemId = 10
                    resumeItemNum = consumeXp - xp
                elif use_item == 2:
                    resumeItemId = 11
                    resumeItemNum = 1
                if items[resumeItemId] > resumeItemNum:
                    raise Exception("item %s not enough" % resumeItemId)
                xp = 0
            else:
                xp = xp - consumeXp

            # calc exp
            add_exp = 0
            for foe_card in foe_band["cards"]:
                if foe_card:
                    battle_exp = card_tbl.get(foe_card["protoId"], "battleExp")
                    add_exp += add_exp

            add_exp_per_card = add_exp/len(members)

            # query card entity info
            cols = ["id", "level", "exp", "protoId", "hp", "atk", "def", "wis", "agi", "hpCrystal", "hpExtra"]
            rows = yield util.whdb.runQuery(
                """ SELECT {} FROM cardEntities
                        WHERE ownerId=%s AND id in ({})""".format(",".join(cols), ",".join(map(str, members)))
                ,(userid, )
            )
            card_entities = [dict(zip(cols, row)) for row in rows]

            # add exp
            levelups = []
            for card_entity in card_entities:
                lvtbl = warlord_level_tbl if card_entity["id"] == warlord else card_level_tbl
                level = card_entity["level"]
                max_level = int(card_tbl.get(card_entity["protoId"], "maxlevel"))
                try:
                    next_lv_exp = int(lvtbl.get(level+1, "exp"))
                    card_entity["exp"] += add_exp_per_card
                    while card_entity["exp"] >= next_lv_exp:
                        level += 1
                        next_lv_exp = int(lvtbl.get(level+1, "exp"))

                    #max level check
                    if level >= max_level:
                        level = max_level
                        card_entity["exp"] = int(lvtbl.get(level, "exp"))

                    #level up
                    if level != card_entity["level"]:
                        hp, atk, dfs, wis, agi = calc_card_proto_attr(card_entity["protoId"], level)
                        card_entity["level"] = level
                        card_entity["hp"] = hp
                        card_entity["atk"] = atk
                        card_entity["def"] = dfs
                        card_entity["wis"] = wis
                        card_entity["agi"] = agi

                        # recover hp
                        new_hp = 0
                        for member in zone_cache["band"]["members"]:
                            if member == card_entity["id"]:
                                new_hp = hp+card_entity["hpCrystal"]+card_entity["hpExtra"]
                                member[1] = new_hp
                                break
                        
                        # 
                        levelup = {}
                        levelup["id"] = card_entity["id"]
                        levelup["level"] = level
                        levelup["exp"] = card_entity["exp"]
                        levelup["hp"] = hp
                        levelup["atk"] = atk
                        levelup["def"] = dfs
                        levelup["wis"] = wis
                        levelup["agi"] = agi
                        levelups.append(levelup)

                        # recover ap and xp
                        if card_entity["id"] == warlord:
                            ap = max_ap
                            xp = max_xp

                except:
                    card_entity["exp"] = int(lvtbl.get(level, "exp"))

            # update cardEntity's attributes
            arg_list = [(c["level"], c["exp"], c["hp"], c["atk"]
                ,c["def"], c["wis"], c["agi"], c["id"]) for c in card_entities]
            yield util.whdb.runOperationMany(
                """UPDATE cardEntities SET level=%s, exp=%s, hp=%s, atk=%s, def=%s, wis=%s, agi=%s
                        WHERE id=%s"""
                ,arg_list
            )

            
            next_pvp_bands = []
            cacheKey = "pvpFoeBands/%s" % userid

            # lose
            if not is_win:
                win_streak = 0
            # win
            else:
                win_streak += 1
                if win_streak % 3 == 0:
                    # fixme: gain reward
                    if win_streak == 30:
                        win_streak = 0

                # next pvp battle
                else:
                    next_pvp_bands, rankrange, score_min, score_max = yield match(pvp_score, win_streak+1, userid)
                    ttl = yield util.redis().ttl(cacheKey)
                    # fixme: use ttl
                    yield util.redis().setex(cacheKey, 600, json.dumps(next_pvp_bands))

            # delete cache if streak break or finish 3 pvps
            if win_streak % 3 == 0:
                yield util.redis().delete(cacheKey)
                

            # update zone cache
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s, xp=%s, lastXpTime=%s, items=%s, pvpWinStreak=%s
                        WHERE userId=%s"""
                ,(json.dumps(zone_cache), xp, last_xp_time, json.dumps(items), win_streak, userid)
            )

            out_members = [{"id":c["id"], "exp":c["exp"]} for c in card_entities]
            
            # reply
            reply = util.new_reply()
            reply["winStreak"] = win_streak
            reply["members"] = out_members
            reply["levelups"] = levelups
            reply["cards"] = []
            reply["items"] = []
            reply["xp"] = xp
            reply["nextAddXpTime"] = nextAddXpTime
            reply["smallXpItemNum"] = items.get(10, 0)
            reply["bigXpItemNum"] = items.get(11, 0)
            reply["nextPvpBands"] = next_pvp_bands
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
    (r"/whapi/pvp/createtestdata", CreateTestData),
    (r"/whapi/pvp/getranks", GetRanks),
    (r"/whapi/pvp/getformula", GetFormula),
    (r"/whapi/pvp/match", Match),
    (r"/whapi/pvp/battleresult", BattleResult),
    (r"/whapi/pvp/test", Test),
    (r"/whapi/pvp/test1", Test1),
    (r"/whapi/pvp/test2", Test2),
    (r"/whapi/pvp/toredis", Toredis),
    (r"/whapi/pvp/toredisa", ToredisAdisp),
    (r"/whapi/pvp/toredisg", ToredisGen),
]

pvp_match_tbl = util.CsvTbl("data/pvpmatch.csv", "id")
pvp_test_data_tbl = util.CsvTbl("data/pvpTestData.csv", "ID")
