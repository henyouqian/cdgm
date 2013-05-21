from error import *
from session import *
from gamedata import BAND_NUM, AP_ADD_DURATION, XP_ADD_DURATION, MONSTER_GROUP_MEMBER_MAX
import util
from card import card_tbl, warlord_level_tbl, card_level_tbl, calc_card_proto_attr

import tornado.web
import adisp
import brukva
import json
import os
from datetime import datetime, timedelta
from random import random, choice


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
                        data = json.load(f)

                        layers = data["layers"]
                        width = data["width"]
                        height = data["height"]
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
        return self.placements[str(zoneid)]["placements"]

class CaseTbl(object):
    def __init__(self):
        cvs_case = util.CsvTbl("data/cases.csv", "ID")
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
        caseId = int(caseId)
        indices, weights = self._t[caseId]
        rdm = WeightedRandom(0, *weights)
        idx = rdm.get()
        return indices[idx]
        

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
        r = -1
        if v == TILE_ALL:
            r = rand1all.get()
        elif v == TILE_ITEM:
            r = rand1item.get()
        elif v == TILE_MON:
            r = rand1mon.get()
        elif v == TILE_START:
            startpos = map(int, k.split(","))
            continue
        elif v == TILE_GOAL:
            goalpos = map(int, k.split(","))
            continue
        if r == 0:      # case or gold
            itemtype = rand2item.get() + 1 # itemtype from 1 to 5
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
               "lastPos":startpos, "redCase":0, "goldCase":0, "monGrpId":-1}
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

    out["startPos"] = dict(zip(["x", "y"], out["startPos"]))
    out["goalPos"] = dict(zip(["x", "y"], out["goalPos"]))
    out["currPos"] = dict(zip(["x", "y"], out["currPos"]))
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
                zoneid = int(self.get_argument("zoneid"))
                bandidx = int(self.get_argument("bandidx"))
                if bandidx not in xrange(BAND_NUM):
                    raise Exception("Bad bandidx")
            except:
                send_error(self, err_param)
                return

            # get player info
            rows = yield util.whdb.runQuery(
                """ SELECT bands, inZoneId, lastZoneId FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            bands = row[0]
            bands = json.loads(bands)
            zone_id = row[1]
            if zone_id != 0:
                raise Exception("Allready in zone")
            last_zone_id = row[2]
            if zoneid > last_zone_id:
                raise Exception("Zone not available")

            # gen cache
            cache = gen_cache(zoneid)

            # band
            band = bands[bandidx]
            members = [mem for mem in band["members"] if mem]

            sql = """ SELECT hp, hpCrystal, hpExtra FROM cardEntities
                        WHERE id IN {} AND ownerId=%s"""
            if len(members) == 1:
                sql = sql.format("(%s)"% members[0])
            else:
                sql = sql.format(str(tuple(members)))
            rows = yield util.whdb.runQuery(
                sql, (userid, )
            )

            if len(rows) != len(members):
                raise Exception("Band member error")
            
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

            # db store
            cachejs = json.dumps(cache)
            row_nums = yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s, inZoneId=%s, currentBand=%s
                        WHERE userid=%s"""
                ,(cachejs, zoneid, bandidx, session["userid"])
            )

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
            row_nums = yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=NULL, inZoneId=0
                        WHERE userid=%s"""
                ,(session["userid"],)
            )

            # reply
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
            rows = yield util.whdb.runQuery(
                """SELECT zoneCache FROM playerInfos 
                        WHERE userid=%s"""
                ,(session["userid"],)
            )
            cache = rows[0][0]

            if not cache:
                raise Exception("Not in zone")
            
            cache = json.loads(cache)
            client_cache = trans_cache_to_client(cache)
            client_cache["error"] = no_error
            self.write(json.dumps(client_cache))

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
            path = json.loads(self.request.body)
            last_xy = None
            for xy in path:
                if last_xy and (abs(last_xy[0]-xy[0]) + abs(last_xy[1]-xy[1]) != 3):
                    raise Exception("dist not 3")
                last_xy = xy
            
            if len(path) < 2:
                raise Exception("path too short")

            last_pos = path[-2]

            # db get cache
            rows = yield util.whdb.runQuery(
                """SELECT zoneCache, ap, maxAp, lastApTime, UTC_TIMESTAMP(), items, money FROM playerInfos 
                        WHERE userid=%s"""
                ,(session["userid"],)
            )
            row = rows[0]
            cache = row[0]
            ap = row[1]
            max_ap = row[2]
            last_ap_time = row[3]
            curr_time = row[4]
            items = row[5]
            money = row[6]

            if not last_ap_time:
                last_ap_time = datetime(2013, 1, 1)

            if not items:
                items = {}
            else:
                items = json.loads(items)

            if not cache:
                raise Exception("Not in zone")
            else:
                cache = json.loads(cache)
            

            # check path
            #check start pos
            currpos = cache["currPos"]
            if currpos != path[0]:
                raise Exception("begin coord not match")

            #update ap
            dt = curr_time - last_ap_time
            dt = int(dt.total_seconds())
            dap = dt // AP_ADD_DURATION
            if dap:
                ap = min(max_ap, ap + dap)
            if ap == max_ap:
                last_ap_time = curr_time
            else:
                last_ap_time = curr_time - timedelta(seconds = dt % AP_ADD_DURATION)
            dt = curr_time - last_ap_time
            nextAddApTime = int(dt.total_seconds())

            if ap == 0:
                send_error(self, "no_ap")
                return

            path = path[1:]
            if len(path) > ap:
                path = path[:ap]

            ap -= len(path)

            # update curr pos
            currpos = cache["currPos"] = path[-1]

            # check and triger event
            currpos = path[-1]
            poskey = "%d,%d" % (currpos[0], currpos[1])
            evtid = cache["objs"].get(poskey)
            item_updated = False
            money_add = 0
            red_case_add = 0
            gold_case_add = 0
            items_add = []
            monGrpId = None
            catch_mons = []
            if evtid:
                del cache["objs"][poskey]
                zoneid = cache["zoneId"]
                maprow = map_tbl.get_row(zoneid)
                if evtid == 10000:      # event
                    pass
                elif evtid < 0:         # battle
                    monGrpId = -evtid
                    cache["monGrpId"] = monGrpId
                    cache["lastPos"] = last_pos
                    row = mongrp_tbl.get_row(monGrpId)
                    catch_prob = float(mongrp_tbl.get_value(row, "catchable"))
                    for i in xrange(10):
                        mon_id = int(mongrp_tbl.get_value(row, "order%d"%(i+1)))
                        if not mon_id:
                            break
                        if random() < catch_prob:
                            catch_mons.append(mon_id)

                    cache["catchMons"] = catch_mons

                elif evtid == 1:    # wood case
                    item_updated = True
                    caseid = map_tbl.get_value(maprow, "woodprobabilityID")
                    itemid = case_tbl.get_item(caseid)
                    print "itemid:", itemid
                    if itemid in items:
                        items[itemid] += 1
                    else:
                        items[itemid] = 1
                    items_add.append({"id":itemid, "num":1})

                elif evtid == 2:    # red case
                    cache["redCase"] += 1
                    red_case_add = 1
                elif evtid == 3:    # gold case
                    cache["goldCase"] += 1
                    gold_case_add = 1
                elif evtid == 4:    # big money
                    money_add = 100
                elif evtid == 5:    # small money
                    money_add = 1000

                if money_add:
                    money += money_add
            
            # update
            cachejs = json.dumps(cache)
            if item_updated:
                itemsjs = json.dumps(items)
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s, ap=%s, lastApTime=%s,
                        money=%s, items=%s
                            WHERE userid=%s"""
                    ,(cachejs, ap, last_ap_time, money, itemsjs, session["userid"])
                )
            else:
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s, ap=%s, lastApTime=%s,
                        money=%s
                            WHERE userid=%s"""
                    ,(cachejs, ap, last_ap_time, money, session["userid"])
                )

            # reply
            reply = util.new_reply()
            reply["currPos"] = dict(zip(["x", "y"], currpos))
            reply["ap"] = ap
            reply["nextAddApTime"] = nextAddApTime
            reply["moneyAdd"] = money_add
            reply["redCaseAdd"] = red_case_add
            reply["goldCaseAdd"] = gold_case_add
            reply["items"] = items_add
            reply["monGrpId"] = monGrpId
            reply["eventId"] = None
            reply["catchMons"] = catch_mons
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
            rows = yield util.whdb.runQuery(
                """ SELECT warlord, zoneCache, items, maxCardNum FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            warlord = row[0]
            cache = json.loads(row[1])
            items = json.loads(row[2])
            max_card_num = row[3]

            band = cache["band"]
            members = band["members"]

            # post input
            input = json.loads(self.request.body)
            inmembers = input["members"]
            if len(inmembers)*2 != len(members):
                raise Exception("Error member num")

            catch_item = input.get("catchItem", 0)

            win = input["isWin"]
            # lost
            if not win:
                if warlord in inmembers:
                    yield util.whdb.runOperation(
                        """UPDATE playerInfos SET inZoneId=0, zoneCache=NULL
                                WHERE userid=%s"""
                        ,(userid,)
                    )
                    reply = util.new_reply()
                    self.write(reply)
                    return

            # win
            # check members valid and store new member status
            mems_per_row = len(inmembers)
            for idx, inmem in enumerate(inmembers):
                if inmem:
                    if inmem["id"] == members[idx][0]:
                        members[idx][1] = inmem["hp"]
                    elif inmem["id"] == members[idx+mems_per_row][0]:
                        members[idx+mems_per_row][1] = inmem["hp"]
                        members[idx], members[idx+mems_per_row] = members[idx+mems_per_row], members[idx]
                    else:
                        raise Exception("Error member pos")
                    if inmem["hp"] > members[idx][1] or inmem["hp"] < 0:
                        raise Exception("Error member hp")
                    if inmem["id"] == warlord and inmem["hp"] == 0:
                        raise Exception("Dead warlord")

            if not win:
                zoneCache["currPos"] = zoneCache["lastPos"]
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s
                            WHERE userId=%s"""
                    ,(json.dumps(cache), userid)
                )

            # add exp
            # calc exp
            mon_grp_id = cache["monGrpId"]
            if mon_grp_id < 0:
                raise Exception("Not in battle")

            row = mongrp_tbl.get_row(str(mon_grp_id))
            cols = ["order%s"%(i+1) for i in xrange(MONSTER_GROUP_MEMBER_MAX)]
            monsters = []
            for col in cols:
                mon = int(mongrp_tbl.get_value(row, col))
                if mon:
                    monsters.append(mon)
            
            exp = 0
            for mon in monsters:
                exp += int(card_tbl.get(mon, "battleExp"))

            # get band card entity
            sql = """SELECT id, level, exp, protoId, hp, atk, def, wis, agi, hpCrystal, hpExtra FROM cardEntities
                        WHERE ownerId=%s AND id in {}"""
            inmembers_alive = [m["id"] for m in inmembers if m and m["hp"] != 0]
            live_num = len(inmembers_alive)
            if live_num == 1:
                sql = sql.format("(%s)"% inmembers_alive[0])
            elif live_num == 0:
                raise Exception("All dead")
            else:
                sql = sql.format(str(tuple(inmembers_alive)))
            rows = yield util.whdb.runQuery(
                sql
                ,(userid, )
            )
            cards = [{"id":row[0], "level":row[1], "exp":row[2], "proto":row[3]
                ,"attrs":[row[4], row[5], row[6], row[7], row[8]]
                ,"hpCrystal":row[9], "hpExtra":row[10]} for row in rows]

            # levelup
            exp_per_card = int(exp / live_num)
            levelups = []
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
                    logging.debug((level, card["level"]))
                    if level != card["level"]:
                        card["level"] = level
                        card["attrs"] = calc_card_proto_attr(card["proto"], level)
                        new_hp = 0
                        for member in members:
                            if member and member[0] == card["id"]:
                                new_hp = card["attrs"][0]+card["hpCrystal"]+card["hpExtra"]
                                member[1] = new_hp
                                break
                        levelup = {}
                        levelup["id"] = card["id"]
                        levelup["level"] = level
                        # levelup.update(dict(zip(["hp", "atk", "def", "wis", "agi"], card["attrs"])))
                        levelups.append(levelup)

                except:
                    card["exp"] = int(lvtbl.get(level, "exp"))

            # catch
            catched_mons = []
            if catch_item in [5, 6]:
                item_num = items.get(str(catch_item), 0)
                if item_num == 0:
                    raise Exception("item not enough")
                catch_mons = cache.get("catchMons")
                if catch_mons:
                    for mon in catch_mons:
                        rarity = mon_card_tbl.get(mon, "rarity")
                        probs = {1:0.5, 2:0.3, 3:0.2, 4:0.1}
                        prob = probs.get(rarity, 0)
                        if random() < prob:
                            catched_mons.append(mon)

                    if catched_mons:
                        catched_mons = yield create_cards(userid, catched_mons, max_card_num, 1)


            # update db
            ## update cardEntities
            arg_list = [(c["level"], c["exp"], c["attrs"][0], c["attrs"][1]
                ,c["attrs"][2], c["attrs"][3], c["attrs"][4], c["id"]) for c in cards]
            row_nums = yield util.whdb.runOperationMany(
                """UPDATE cardEntities SET level=%s, exp=%s, hp=%s, atk=%s, def=%s, wis=%s, agi=%s
                        WHERE id=%s"""
                ,arg_list
            )

            ## update band infos in zoneCache
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s
                        WHERE userId=%s"""
                ,(json.dumps(cache), userid)
            )

            # reply
            reply = util.new_reply()
            members = []
            for card in cards:
                member = {}
                member["id"] = card["id"]
                member["exp"] = card["exp"]
                members.append(member)

            reply["members"] = members
            reply["levelups"] = levelups
            reply["catchedMons"] = catched_mons
            self.write(json.dumps(reply))
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
            rows = yield util.whdb.runQuery(
                """ SELECT zoneCache, items, lastZoneId, maxCardNum, maxTradeNum, lastFormation FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            if not row[0]:
                raise Exception("not in zone")
            cache = json.loads(row[0])
            items = json.loads(row[1])
            last_zoneid = row[2]
            max_card_num = row[3]
            max_trade_num = row[4]
            last_formation = row[5]

            if cache["currPos"] != cache["goalPos"]:
                raise Exception("palyer not at goal pos")

            # open cases
            zoneid = cache["zoneId"]
            maprow = map_tbl.get_row(zoneid)
            
            red_case_items = []
            gold_case_items = []

            # red case
            for x in xrange(cache["redCase"]):
                caseid = map_tbl.get_value(maprow, "treasureprobabilityID")
                itemid = case_tbl.get_item(caseid)
                if itemid in items:
                    items[itemid] += 1
                else:
                    items[itemid] = 1
                red_case_items.append(int(itemid))

            # gold case
            for x in xrange(cache["goldCase"]):
                caseid = map_tbl.get_value(maprow, "chestprobabilityID")
                itemid = case_tbl.get_item(caseid)
                if itemid in items:
                    items[itemid] += 1
                else:
                    items[itemid] = 1
                gold_case_items.append(int(itemid))

            # if first time complete
            new_last_zone_id = None
            new_max_card_num = None
            new_max_trade_num = None
            new_last_formation = None

            if last_zoneid == zoneid:
                # find new zone id
                num = int(zone_tbl.get(zoneid, "nextZoneId"))
                if num and num > last_zoneid:
                    new_last_zone_id = last_zoneid = num

                # reward event
                evtid = map_tbl.get_value(maprow, "rewardeventID")
                evtrow = evt_tbl.get_row(evtid)

                ## reward items
                rwditems = []
                for i in xrange(3):
                    itemid = int(evt_tbl.get_value(evtrow, "item%dID"%(i+1)))
                    itemnum = int(evt_tbl.get_value(evtrow, "amount%d"%(i+1)))
                    if itemid and itemnum:
                        if itemid in items:
                            items[itemid] += itemnum
                        else:
                            items[itemid] = itemnum
                        for item in rwditems:
                            rwditems.append(item)

                ## reward cards
                rwdcards = []
                for i in xrange(3):
                    cardid = int(evt_tbl.get_value(evtrow, "card%dID"%(i+1)))
                    if cardid:
                        rwdcards.append(cardid)
                if rwdcards:
                    rwdcards = yield create_cards(userid, rwdcards, max_card_num, 1)

                ## reward max card number
                num = int(evt_tbl.get_value(evtrow, "maxcardnum"))
                if num and num > max_card_num:
                    new_max_card_num = max_card_num = num

                ## reward max trade number
                num = int(evt_tbl.get_value(evtrow, "maxtreadnum"))
                if num and num > max_trade_num:
                    new_max_trade_num = max_trade_num = num

                ## reward formation
                num = int(evt_tbl.get_value(evtrow, "band"))
                if num and num > last_formation:
                    new_last_formation = last_formation = num

            # db store
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=NULL, inZoneId=0, items=%s, lastZoneId=%s
                    , maxCardNum=%s, maxTradeNum=%s, lastFormation=%s
                    WHERE userid=%s"""
                ,(json.dumps(items), last_zoneid, max_card_num, max_trade_num, last_formation, session["userid"])
            )

            # response
            reply = {"error": no_error}
            reply["redCase"] = red_case_items
            reply["goldCase"] = gold_case_items
            reply["items"] = rwditems
            reply["cards"] = rwdcards
            reply["lastZoneId"] = new_last_zone_id
            reply["formation"] = new_last_formation
            reply["maxCardNum"] = new_max_card_num
            reply["maxTradeNum"] = new_max_trade_num
            

            self.write(json.dumps(reply))
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

map_tbl = util.CsvTbl("data/maps.csv", "zoneID")
plc_tbl = PlacementTbl()
mongrp_tbl = util.CsvTbl("data/monsters.csv", "ID")
case_tbl = CaseTbl()
zone_tbl = util.CsvTbl("data/zones.csv", "id")
mon_card_tbl = util.CsvTbl("data/monstercards.csv", "ID")
evt_tbl = util.CsvTbl("data/events.csv", "ID")

# =============================================
if __name__ == "__main__":
    out = gen_cache("50101")
    print out