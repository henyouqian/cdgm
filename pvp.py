from session import find_session
from error import *
import util
from card import card_tbl, skill_tbl

import tornado.web
import adisp

import json
import random
import datetime

PVP_ID_SERIAL = "PVP_ID_SERIAL"
PVP_Z_KEY = "PVP_Z_KEY"
PVP_H_KEY = "PVP_H_KEY"

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
        card key: protoId, hp, atk, def, agi, wis
    """
    card_proto = card_tbl.get_row(card["protoId"])
    price, skillid1, skillid2, skillid3 = map(int, card_tbl.get_values("price", "skill1Id", "skill2Id", "skill3Id"))

    skillRaritySum = 0
    for skillid in [skillid1, skillid2, skillid3]:
        if skillid:
            skillRaritySum += skill_tbl.get(skillid, "rarity")

    score = card["hp"] + card["atk"] + card["def"] + card["agi"] + card["wis"]
    score += int((price * skillRaritySum) * 0.1)
    return score


def calc_player_pvp_score(userid, bands, cards):
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
def upload_pvp_band(userid, username, cards, callback):
    """
        card key: protoId, level, hp, atk, def, agi, wis, skill1Id, skill1Level, skill2Id, skill2Level, skill3Id, skill3Level
    """
    try:
        # calc pvp score
        pvp_score = 0
        for card in cards:
            if card:
                score = calc_pvp_score(card)
                pvp_score += score

        # update to redis
        pipe = util.redis_pipe()
        pipe.zadd(PVP_Z_KEY, pvp_score, userid)

        pvp_data = {"username": username, "band":cards, "score": pvp_score}
        pipe.hset(PVP_H_KEY, userid, json.dumps(pvp_data))
        yield util.redis_pipe_execute(pipe)
        callback(None)

    except Exception as e:
        callback(e)


@adisp.async
@adisp.process
def upload_pvp_band(userid, username, cards, callback):
    pass

handlers = [
    (r"/whapi/pvp/addtestrecord", AddTestRecord),
]
