from error import *
from session import *
from gamedata import BAND_NUM
import g
from util import CsvTbl
from card import card_tbl, warlord_level_tbl, card_level_tbl, calc_card_proto_attr

import tornado.web
import adisp
import brukva
import simplejson as json
import os
from datetime import datetime, timedelta
from random import random, choice

import tornadoredis


TILE_ALL = 4        # tile index in tiled(the editor), gen item or monster
TILE_ITEM = 5       # tile index which generate item only
TILE_MON = 6        # tile index which generate monster only
TILE_START = 2      # start tile
TILE_GOAL = 3       # goal tile


class PlacementTbl(object):
    def __init__(self):
        for root, dirs, files in os.walk('data/map'):
            self.placements = {}
            for filename in files:
                nameext = filename.split(".")
                if nameext[-1] == "json" and len(nameext) == 2:
                    path = root + "/" + filename
                    zoneid = nameext[0]
                    with open(path, "rb") as f:
                        root = json.load(f)

                        layers = root["layers"]
                        width = root["width"]
                        height = root["height"]
                        zone = {"width":width, "height":height}
                        for layer in layers:
                            if layer["name"] == "event":
                                zone["placements"] = self._parse_placement_conf(layer["data"], width, height)

                        self.placements[zoneid] = zone
            break


    def _parse_placement_conf(self, data, width, height):
        tiles = width * height
        if len(data) != tiles:
            raise Exception("Path data length error")
        i = 0
        out = {}
        for d in data:
            if d:
                x = i % width
                y = i / width
                out["{},{}".format(x, y)] = d
            i = i + 1
        return out

    def get_zone_data(self, zoneid):
        return self.placements[zoneid]["placements"]

class CaseTbl(object):
    def __init__(self):
        cvs_case = CsvTbl("data/cases.csv", "ID")
        self._t = {}
        for k, v in cvs_case.body.iteritems():
            row = v[1:]
            indices = []
            weights = []
            for idx, weight in enumerate(row):
                w = float(weight)
                if w > 0:
                    indices.append(idx+1)
                    weights.append(w)
            self._t[int(k)] = (indices, weights)

    def get_item(self, caseId):
        try:
            indices, weights = self._t[caseId]
            rdm = WeightedRandom(0, *weights)
            idx = rdm.get()          
            return indices[idx]
        except:
            return 0
        

class WeightedRandom(object):
    def __init__(self, totalWeight, *weights):
        """if totalWeight <= 0, auto sum weights as totalWeight"""
        sum = 0
        uppers = []
        for weight in weights:
            sum += weight
            uppers.append(sum)
        if totalWeight > 0:
            sum = totalWeight
        self.uppers = [x/float(sum) for x in uppers]

    def get(self):
        rdm = random()
        idx = 0
        for upper in self.uppers:
            if rdm <= upper:
                return idx
            idx += 1
        return -1

def gen_cache(zoneid):
    tiles = plc_tbl.get_zone_data(zoneid)
    maprow = map_tbl.get_row(zoneid)
    itemrate = float(map_tbl.get_value(maprow, "item%"))
    monsterrate = float(map_tbl.get_value(maprow, "monster%"))
    eventrate = float(map_tbl.get_value(maprow, "event%"))

    rand1all = WeightedRandom(1.0, itemrate, monsterrate, eventrate)
    rand1item = WeightedRandom(1.0, itemrate + monsterrate, 0, eventrate)
    rand1mon = WeightedRandom(1.0, 0, itemrate + monsterrate, eventrate)

    woodrate = float(map_tbl.get_value(maprow, "wood%"))
    treasurerate = float(map_tbl.get_value(maprow, "treasure%"))
    chestrate = float(map_tbl.get_value(maprow, "chest%"))
    littlegoldrate = float(map_tbl.get_value(maprow, "littlegold%"))
    biggoldrate = float(map_tbl.get_value(maprow, "biggold%"))

    rand2item = WeightedRandom(1.0, woodrate, treasurerate, chestrate, littlegoldrate, biggoldrate)

    mongrpids = []
    for i in xrange(1, 11):
        monid = map_tbl.get_value(maprow, "monster%dID" % i)
        if monid != "0":
            mongrpids.append(monid)
        else:
            break

    objs = {}
    startpos = None
    goalpos = None
    for k, v in tiles.iteritems():
        r = 0
        if v == TILE_ALL:
            r = rand1all.get()
        elif v == TILE_ITEM:
            r = rand1item.get()
        elif v == TILE_MON:
            r = rand1mon.get()
        elif v == TILE_START:
            startpos = dict(zip(("x", "y"), map(int, k.split(","))))
            continue
        elif v == TILE_GOAL:
            goalpos = dict(zip(("x", "y"), map(int, k.split(","))))
            continue

        if r == 0:      # item
            itemtype = rand2item.get()
            if itemtype >= 0:
                objs[k] = itemtype
        elif r == 1:    # battle
            grpid = choice(mongrpids)
            # row = mongrp_tbl.get_row(grpid)
            # img = mongrp_tbl.get_value(row, "image")
            # objs[k] = -int(img)
            objs[k] = -int(grpid)
        elif r == 2:    # event
            objs[k] = 10000


    cache = {"zoneId":int(zoneid), "objs":objs, "startPos":startpos, "goalPos":goalpos, "currPos":startpos, 
                "redCase":0, "goldCase":0, "monGrpId":-1}
    return cache

# =============================================
def trans_cache_to_client(cache):
    out = cache
    objs = cache["objs"]
    outobjs = []
    for k, v in objs.iteritems():
        elem = k.split(",")
        elem = map(int, elem)
        elem.append(v)
        outobjs.append(elem)
    out["objs"] = outobjs

    band = cache["band"]
    outband = {"formation":band["formation"]}
    outband["members"] = [{"id": m[0], "hp":m[1]} if m else None for m in band["members"]]
    out["band"] = outband
    return out

class Enter(tornado.web.RequestHandler):
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
            # param
            try:
                zoneid = self.get_argument("zoneid")
                bandidx = self.get_argument("bandidx")
                if int(bandidx) not in xrange(BAND_NUM):
                    raise Exception("Bad bandidx")
            except:
                send_error(self, err_param)
                return
            # gen
            try:
                cache = gen_cache(zoneid)
            except:
                send_error(self, err_not_exist)

            # band
            try:
                rows = yield g.whdb.runQuery(
                    """ SELECT bands FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, )
                )
                row = rows[0]
                bands = row[0]
                bands = json.loads(bands)
            except:
                send_error(self, err_db)
                return

            band = bands[int(bandidx)]
            members = [mem for mem in band["members"] if mem]

            try:
                sql = """ SELECT hp, hpCrystal, hpExtra FROM cardEntities
                            WHERE id IN {} AND ownerId=%s"""
                if len(members) == 1:
                    sql = sql.format("(%s)"% members[0])
                else:
                    sql = sql.format(str(tuple(members)))
                rows = yield g.whdb.runQuery(
                    sql, (userid, )
                )
            except:
                send_error(self, err_db)
                return

            if len(rows) != len(members):
                send_error(self, "err_member")
                return
            
            hps = [sum(row) for row in rows]
            mem_hp = dict(zip(members, hps))
            new_members = []
            for member in band["members"]:
                if member:
                    new_members.append((member, mem_hp[member]))
                else:
                    new_members.append(None)
            
            band["members"] = new_members
            cache["band"] = band

            # # redis store
            # key = str(session["userid"])+"/zonecache"
            # yield g.redis().delete(key)
            # rv = yield g.redis().hmset(key, cache)
            # if not rv:
            #     send_error(self, err_redis)
            #     return

            # db store
            cachejs = json.dumps(cache)
            try:
                row_nums = yield g.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s, isInZone=1
                            WHERE userid=%s"""
                    ,(cachejs, session["userid"])
                )
            except:
                send_error(self, err_db)
                return

            # response
            clientCache = trans_cache_to_client(cache)
            clientCache["error"] = no_error
            reply = json.dumps(clientCache)
            self.write(reply)
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Withdraw(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return

            # db store
            try:
                row_nums = yield g.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=NULL, isInZone=0
                            WHERE userid=%s"""
                    ,(session["userid"],)
                )
            except:
                send_error(self, err_db)
                return

            # response
            send_ok(self)

        except:
            send_internal_error(self)
        finally:
            self.finish()

class Get(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return

            # db get
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT zoneCache FROM playerInfos 
                            WHERE userid=%s"""
                    ,(session["userid"],)
                )
                cache = rows[0][0]
            except:
                send_error(self, err_db)
                return

            if not cache:
                send_error(self, err_not_exist)
                return
            
            cache = json.loads(cache)
            clientCache = trans_cache_to_client(cache)
            clientCache["error"] = no_error
            rspJs = json.dumps(clientCache)
            self.write(rspJs)

        except:
            send_internal_error(self)
        finally:
            self.finish()

class Move(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return

            # post input
            path = []
            try:
                path = json.loads(self.request.body)
                last_xy = None
                for xy in path:
                    if last_xy and (abs(last_xy[0]-xy[0]) + abs(last_xy[1]-xy[1]) != 3):
                        raise Exception("dist not 3")
                    last_xy = xy
                
                if len(path) < 2:
                    raise Exception("path too short")

            except:
                send_error(self, err_post)
                return

            # db get cache
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT zoneCache, xp, maxXp, lastXpTime, UTC_TIMESTAMP(), items, gold FROM playerInfos 
                            WHERE userid=%s"""
                    ,(session["userid"],)
                )
                row = rows[0]
                cache = row[0]
                xp = row[1]
                max_xp = row[2]
                last_xp_time = row[3]
                curr_time = row[4]
                items = row[5]
                gold = row[6]

                if not last_xp_time:
                    last_xp_time = datetime(2013, 1, 1)

                if not items:
                    items = {}
                else:
                    items = json.loads(items)

                if not cache:
                    send_error(self, "err_no_cache")
                    return
                else:
                    cache = json.loads(cache)

            except:
                send_error(self, err_db)
                return

            

            # check path
            try:
                #check start pos
                currpos = cache["currPos"]
                currpos = [currpos["x"], currpos["y"]]
                if currpos != path[0]:
                    raise Exception("begin coord not match")

                #update xp
                dt = curr_time - last_xp_time
                dt = int(dt.total_seconds())
                xp_add_duration = 10
                dxp = dt // xp_add_duration
                if dxp:
                    xp = min(max_xp, xp + dxp)
                if xp == max_xp:
                    last_xp_time = curr_time
                else:
                    last_xp_time = curr_time - timedelta(seconds = dt % xp_add_duration)

                if xp == 0:
                    send_error(self, "no_xp")
                    return

                path = path[1:]
                if len(path) > xp:
                    path = path[:xp]

                xp -= len(path)
            except:
                send_error(self, err_post)
                return

            # check event exist
            currpos = path[-1]
            poskey = "%d,%d" % (currpos[0], currpos[1])
            evtid = cache["objs"].get(poskey)
            item_updated = False
            gold_add = 0
            red_case_add = 0
            gold_case_add = 0
            items_add = []
            monGrpId = None
            if evtid:
                del cache["objs"][poskey]
                zoneid = cache["zoneId"]
                maprow = map_tbl.get_row(zoneid)
                if evtid == 10000:      # event
                    pass
                elif evtid < 0:         # battle
                    cache["monGrpId"] = -evtid
                    # monrow = mongrp_tbl.get_row(str(-evtid))
                    # img = mongrp_tbl.get_value(monrow, "image")
                    # fixme
                elif evtid == 1:    # wood case
                    caseid = map_tbl.get_value(maprow, "woodprobabilityID")
                    itemid = case_tbl.get_item(caseid)
                    if itemid in items:
                        items[itemid] += 1
                    else:
                        items[itemid] = 1
                    item_updated = True
                    items_add.append({"id":itemid, "num":1})
                elif evtid == 2:    # red case
                    cache["redCase"] += 1
                    red_case_add = 1
                elif evtid == 3:    # golden case
                    cache["goldCase"] += 1
                    gold_case_add = 1
                elif evtid == 4:
                    gold_add = 100
                elif evtid == 5:
                    gold_add = 1000

                if gold_add:
                    gold += gold_add
            
            # update
            cache["currPos"] = {"x":currpos[0], "y":currpos[1]}
            cachejs = json.dumps(cache)
            try:
                if item_updated:
                    itemsjs = json.dumps(items)
                    yield g.whdb.runOperation(
                        """UPDATE playerInfos SET zoneCache=%s, xp=%s, lastXpTime=%s,
                            gold=%s, items=%s
                                WHERE userid=%s"""
                        ,(cachejs, xp, last_xp_time, gold, itemsjs, session["userid"])
                    )
                else:
                    yield g.whdb.runOperation(
                        """UPDATE playerInfos SET zoneCache=%s, xp=%s, lastXpTime=%s,
                            gold=%s
                                WHERE userid=%s"""
                        ,(cachejs, xp, last_xp_time, gold, session["userid"])
                    )
            except:
                send_error(self, err_db)
                return

            # reply
            reply = {"error":no_error, "pos":currpos}
            reply["xp"] = xp
            reply["lastXpTime"] = last_xp_time
            reply["gold"] = gold_add
            reply["redCase"] = red_case_add
            reply["goldCase"] = gold_case_add
            reply["items"] = items_add
            reply["monGrpId"] = monGrpId
            reply["eventId"] = None

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

            # get player info
            try:
                rows = yield g.whdb.runQuery(
                    """ SELECT warlord, zoneCache FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, )
                )
                row = rows[0]
                warlord = row[0]
                cache = row[1]
                cache = json.loads(cache)
            except:
                send_error(self, err_db)
                return

            band = cache["band"]
            members = [m for m in band[1:]]

            # post input
            input = json.loads(self.request.body)

            win = input["isWin"]
            if not win:
                try:
                    yield g.whdb.runOperation(
                        """UPDATE playerInfos SET isInZone=0, zoneCache=NULL
                                WHERE userid=%s"""
                        ,(userid,)
                )
                except:
                    send_error(self, err_db)
                    return
                reply = {"error":no_error}
                self.write(reply)
                return

            # win
            # check members valid and store new member status
            try:
                inmembers = input["members"]
                if len(inmembers)*2 != len(members):
                    raise Exception("Error member num")

                mems_per_row = len(inmembers)
                for idx, inmem in enumerate(inmembers):
                    if inmem:
                        if inmem[0] == members[idx][0]:
                            members[idx] = inmem[:]
                        elif inmem[0] == members[idx+mems_per_row][0]:
                            members[idx+mems_per_row] = inmem[:]
                            members[idx], members[idx+mems_per_row] = members[idx+mems_per_row], members[idx]
                        else:
                            raise Exception("Error member pos")
                        if inmem[1] > members[idx][1] or inmem[1] < 0:
                            raise Exception("Error member hp")
                        if inmem[0] == warlord and inmem[1] == 0:
                            raise Exception("Dead warlord")

            except:
                send_error(self, "err_member")
                return

            # add exp
            try:
                # calc exp
                mon_grp_id = cache["monGrpId"]
                row = mongrp_tbl.get_row(str(mon_grp_id))
                cols = ["order%sID"%(i+1) for i in xrange(10)]
                monsters = []
                for col in cols:
                    mon = int(mongrp_tbl.get_value(row, col))
                    if mon:
                        monsters.append(mon)
                
                exp = 0
                for mon in monsters:
                    exp += int(card_tbl.get(mon, "battleExp"))

                try:
                    # get band card entity
                    sql = """SELECT id, level, exp, protoId, hp, atk, def, wis, agi FROM cardEntities
                                WHERE ownerId=%s AND id in {}"""
                    inmembers_alive = [m[0] for m in inmembers if m and m[1] != 0]
                    live_num = len(inmembers_alive)
                    if live_num == 1:
                        sql = sql.format("(%s)"% inmembers_alive[0])
                    elif live_num == 0:
                        raise Exception("All dead")
                    else:
                        sql = sql.format(str(tuple(inmembers_alive)))
                    rows = yield g.whdb.runQuery(
                        sql
                        ,(userid, )
                    )
                    cards = [{"id":row[0], "level":row[1], "exp":row[2], "proto":row[3]
                        ,"attrs":[row[4], row[5], row[6], row[7], row[8]]} for row in rows]
                    
                except:
                    send_error(self, err_db)
                    return

                exp_per_card = int(exp / live_num)
                for card in cards:
                    lvtbl = warlord_level_tbl if card["id"] == warlord else card_level_tbl
                    level = card["level"]
                    max_level = int(card_tbl.get(card["proto"], "maxlevel"))
                    try:
                        next_lv_exp = int(lvtbl.get(level+1, "exp"))
                        card["exp"] += exp_per_card
                        while card["exp"] >= next_lv_exp:
                            level += 1
                            next_lv_exp = int(lvtbl.get(level, "exp"))

                        #max level check
                        if level >= max_level:
                            level = max_level
                            card["exp"] = int(lvtbl.get(level, "exp"))

                        #level up
                        if level != card["level"]:
                            card["level"] = level
                            card["attrs"] = calc_card_proto_attr(card["proto"], level)
                    except:
                        card["exp"] = int(lvtbl.get(level, "exp"))

                # update db
                try:
                    arg_list = [(c["level"], c["exp"], c["attrs"][0], c["attrs"][1]
                        ,c["attrs"][2], c["attrs"][3], c["attrs"][4], c["id"]) for c in cards]
                    row_nums = yield g.whdb.runOperationMany(
                        """UPDATE cardEntities SET level=%s, exp=%s, hp=%s, atk=%s, def=%s, wis=%s, agi=%s
                                WHERE id=%s"""
                        ,arg_list
                    )
                except:
                    send_error(self, err_db)
                    return
            except:
                send_error(self, "err_add_exp")
                return

            send_ok(self)
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Complete(tornado.web.RequestHandler):
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
            
            # get player info
            try:
                rows = yield g.whdb.runQuery(
                    """ SELECT zoneCache FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, )
                )
                row = rows[0]
                warlord = row[0]
                cache = row[1]
                cache = json.loads(cache)
            except:
                send_error(self, err_db)
                return

            # open cases

            # unlock new zone

            # db store
            try:
                row_nums = yield g.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=NULL, isInZone=0
                            WHERE userid=%s"""
                    ,(session["userid"],)
                )
            except:
                send_error(self, err_db)
                return

            # response
            send_ok(self)

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/zone/enter", Enter),
    (r"/whapi/zone/withdraw", Withdraw),
    (r"/whapi/zone/get", Get),
    (r"/whapi/zone/move", Move),
    (r"/whapi/zone/battleresult", BattleResult),
    (r"/whapi/zone/complete", Complete),
]

map_tbl = CsvTbl("data/maps.csv", "zoneID")
plc_tbl = PlacementTbl()
mongrp_tbl = CsvTbl("data/monsters.csv", "ID")
case_tbl = CaseTbl()

# =============================================
if __name__ == "__main__":
    out = gen_cache("50101")
    print out