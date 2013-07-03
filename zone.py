from error import *
from session import *
from gamedata import BAND_NUM, AP_ADD_DURATION, \
    XP_ADD_DURATION, MONSTER_GROUP_MEMBER_MAX, MONEY_BAG_SMALL_ID, MONEY_BAG_BIG_ID, RED_CASE_ID, GOLD_CASE_ID
import util
from card import card_tbl, warlord_level_tbl, card_level_tbl, calc_card_proto_attr
from player import fmt_tbl

import tornado.web
import adisp
import brukva
import json
import os
import logging
from datetime import datetime, timedelta
from random import random, choice


TILE_ALL = 4        # tile index in tiled(the editor), gen item or monster
TILE_ITEM = 5       # tile index which generate item only
TILE_MON = 6        # tile index which generate monster only
TILE_START = 2      # start tile
TILE_GOAL = 3       # goal tile

TILE_EVENT_RANGE = xrange(11, 21)



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

def gen_cache(zoneid, islastZone):
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
    events = {}
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
        elif v > 10:    # event
            try:
                event_id = int(map_evt_tbl.get((zoneid, v), "eventid"))
                is_repeat = int(evt_tbl.get(event_id, "repeat"))
                if islastZone or is_repeat:
                    events[k] = event_id
            except:
                logging.error("map_evt_tbl error: mapid=%d, tilevalue=%d" % (zoneid, v))
            continue
        if r == 0:      # case or gold
            itemtype = rand2item.get() + 1 # itemtype from 1 to 5
            if itemtype >= 0:
                objs[k] = itemtype
        elif r == 1:    # battle
            if mongrpids:
                grpid = choice(mongrpids)
                objs[k] = -int(grpid)
        elif r == 2:    # event
            objs[k] = 10000


    cache = {"zoneId":zoneid, "objs":objs, "startPos":startpos, "goalPos":goalpos, "currPos":startpos, 
               "lastPos":startpos, "redCase":0, "goldCase":0, "monGrpId":-1, "events":events}
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

    events = cache["events"]
    outevents = []
    for pos, eventid in events.iteritems():
        try:
            pt = [int(p) for p in pos.split(",")]
            start_dialog, end_dialog, monsterid = evt_tbl.gets(eventid, "startdialogueID", "overdialogueID", "monsterID")
            event = {"x": pt[0], "y": pt[1], "startDialog": int(start_dialog), "endDialog": int(end_dialog), "monsterId": int(monsterid)}
            outevents.append(event)
        except:
            logging.error("event parse error: %s", traceback.format_exc())

    out["events"] = outevents

    # dialogue
    enter_diag, complete_diag = map(int, map_tbl.gets(cache["zoneId"], "enterzonerdialogueID", "completezonedialogueID"))
    out["enterDialogue"] = enter_diag
    out["completeDialogue"] = complete_diag

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
            in_zone_id = row[1]
            if in_zone_id != 0:
                raise Exception("Allready in zone")
            last_zone_id = row[2]
            if zoneid > last_zone_id:
                raise Exception("Zone not available")

            # gen cache
            isLastZone = (zoneid == last_zone_id)
            cache = gen_cache(zoneid, isLastZone)

            # band
            band = bands[bandidx]
            memids = [mem for mem in band["members"] if mem]

            sql = """ SELECT id, hp, hpCrystal, hpExtra FROM cardEntities
                        WHERE id IN ({}) AND ownerId=%s""".format(",".join((str(m) for m in memids)))
            rows = yield util.whdb.runQuery(
                sql, (userid, )
            )

            if len(rows) != len(memids):
                raise Exception("Band member error")
            
            dict_id_hp = {}
            for row in rows:
                hpsum = sum(row[1:])
                dict_id_hp[row[0]] = hpsum

            new_members = []
            for memid in band["members"]:
                if memid:
                    new_members.append((memid, dict_id_hp[memid]))
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

def getMoneyNum(bag_type):
    if bag_type == MONEY_BAG_SMALL_ID:
        return 100
    elif bag_type == MONEY_BAG_BIG_ID:
        return 1000

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
            userid = session["userid"]

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
                """SELECT zoneCache, ap, maxAp, lastApTime, UTC_TIMESTAMP(), items, money, maxCardNum FROM playerInfos 
                        WHERE userid=%s"""
                ,(userid,)
            )
            row = rows[0]
            cache = row[0]
            ap = row[1]
            max_ap = row[2]
            last_ap_time = row[3]
            curr_time = row[4]
            items = row[5]
            money = row[6]
            max_card_num = row[7]

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
            # check start pos
            currpos = cache["currPos"]
            if currpos != path[0]:
                raise Exception("begin coord not match: currpos=%s, path=%s" %(str(currpos), str(path)))

            # update ap
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

            # path = path[1:]
            step_num = len(path) - 1
            if step_num > ap:
                path = path[:ap]

            ap -= step_num 

            # update curr pos
            currpos = cache["currPos"] = path[-1]

            # check and triger battles and get items
            poskey = "%d,%d" % (currpos[0], currpos[1])
            evtid = cache["objs"].get(poskey)
            money_add = 0
            red_case_add = 0
            gold_case_add = 0
            items_add = []
            monGrpId = None
            catch_mons = []
            if evtid:
                zoneid = cache["zoneId"]
                maprow = map_tbl.get_row(zoneid)
                if evtid == 10000:      # event
                    pass
                elif evtid < 0:         # battle
                    monGrpId = -evtid
                elif evtid == 1:    # wood case
                    caseid = map_tbl.get_value(maprow, "woodprobabilityID")
                    itemid = case_tbl.get_item(caseid)
                    items_add.append({"id":itemid, "num":1})
                elif evtid == 2:    # red case
                    items_add.append({"id":RED_CASE_ID, "num":1})
                elif evtid == 3:    # gold case
                    items_add.append({"id":GOLD_CASE_ID, "num":1})
                elif evtid == 4:    # small money bag
                    items_add.append({"id":MONEY_BAG_SMALL_ID, "num":1})
                elif evtid == 5:    # big money bag
                    items_add.append({"id":MONEY_BAG_BIG_ID, "num":1})

                if money_add:
                    money += money_add

            # event
            events = cache["events"]
            eventid = events.get(poskey)
            evt_cards = []
            if eventid:
                monsterid, itemid1, itemnum1, itemid2, itemnum2, itemid3, itemnum3, cardid1, cardid2, cardid3 = \
                    evt_tbl.gets(eventid, "monsterID", "item1ID", "amount1", "item2ID", "amount2", "item3ID", "amount3", "card1ID", "card2ID", "card3ID")
                monsterid = int(monsterid)
                if monsterid:
                    monGrpId = monsterid
                else:
                    evt_items = [{"id":int(itemid1), "num":int(itemnum1)}, {"id":int(itemid2), "num":int(itemnum2)}, {"id":int(itemid3), "num":int(itemnum3)}]
                    evt_cards = [int(cardid1), int(cardid2), int(cardid3)]
                    for item in evt_items:
                        if item["id"]:
                            items_add.append(item)
                    evt_cards = [card for card in evt_cards if card]

            # add items
            _items_add = []
            for item in items_add:
                itemid = item["id"]
                itemnum = item["num"]
                if itemid == MONEY_BAG_SMALL_ID:
                    n = getMoneyNum(MONEY_BAG_SMALL_ID)
                    money_add += n
                elif itemid == MONEY_BAG_BIG_ID:
                    n = getMoneyNum(MONEY_BAG_BIG_ID)
                    money_add += n
                elif itemid == RED_CASE_ID:
                    cache["redCase"] += itemnum
                    red_case_add += itemnum
                    continue
                elif itemid == GOLD_CASE_ID:
                    cache["goldCase"] += itemnum
                    gold_case_add += itemnum
                    continue
                else:
                    if itemid in items:
                        items[itemid] += itemnum
                    else:
                        items[itemid] = itemnum
                _items_add.append(item)
            items_add = _items_add

            # add cards
            if evt_cards:
                cards = yield create_cards(userid, evt_cards, max_card_num, 1)

            # battle
            if monGrpId:
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

                cache["battlePos"] = currpos
                currpos = cache["currPos"] = path[-2]

            elif evtid:
                del cache["objs"][poskey]

            # update
            cachejs = json.dumps(cache)
            itemsjs = json.dumps(items)
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s, ap=%s, lastApTime=%s,
                    money=%s, items=%s
                        WHERE userid=%s"""
                ,(cachejs, ap, last_ap_time, money, itemsjs, userid)
            )

            # reply
            reply = util.new_reply()
            reply["currPos"] = dict(zip(["x", "y"], currpos))
            reply["ap"] = ap
            reply["nextAddApTime"] = nextAddApTime
            reply["redCaseAdd"] = red_case_add
            reply["goldCaseAdd"] = gold_case_add
            reply["items"] = items_add
            reply["cards"] = evt_cards
            reply["monGrpId"] = monGrpId
            reply["eventId"] = eventid
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
                """ SELECT warlord, zoneCache, items, maxCardNum, ap, maxAp FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            warlord = row[0]
            cache = json.loads(row[1])
            items = json.loads(row[2])
            max_card_num = row[3]
            ap = row[4]
            max_ap = row[5]

            band = cache["band"]
            members = band["members"]

            # post input
            input = json.loads(self.request.body)
            inmembers = input["members"]
            memid_list = [mem["id"] for mem in inmembers if mem]
            if len(inmembers)*2 != len(members):
                raise Exception("Error member num")

            catch_item = input.get("catchItem", 0)

            win = input["isWin"]

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
                    if win and inmem["id"] == warlord and inmem["hp"] == 0:
                        raise Exception("Dead warlord")

            # del obj in this tile
            currpos = cache["currPos"] = cache["battlePos"]
            poskey = "%d,%d" % (currpos[0], currpos[1])
            if poskey in cache["objs"]:
                del cache["objs"][poskey]

            # lost
            if not win:
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s
                            WHERE userId=%s"""
                    ,(json.dumps(cache), userid)
                )
                reply = util.new_reply()
                reply["members"]=[]
                reply["levelups"]=[]
                reply["catchedMons"]=[]
                reply["items"] = []
                reply["cards"] = []
                reply["currPos"] = cache["currPos"]
                self.write(reply)
                return

            # add exp
            # calc exp
            mon_grp_id = cache["monGrpId"]
            if mon_grp_id < 0:
                raise Exception("Not in battle")

            row = mongrp_tbl.get_row(str(mon_grp_id))
            cols = ["order%slevel"%(i+1) for i in xrange(MONSTER_GROUP_MEMBER_MAX)]
            exp = 0
            for col in cols:
                level = int(mongrp_tbl.get_value(row, col))
                if level:
                    exp += level

            # get band card entity
            is_warlord_appended = False
            sql = """SELECT id, level, exp, protoId, hp, atk, def, wis, agi, hpCrystal, hpExtra FROM cardEntities
                        WHERE ownerId=%s AND id in ({})"""
            inmembers_alive = [m["id"] for m in inmembers if m and m["hp"] != 0]
            live_num = len(inmembers_alive)
            if live_num == 0:
                raise Exception("All dead")
            else:
                if warlord not in inmembers_alive:
                    inmembers_alive.append(warlord) # append warlord
                    is_warlord_appended = True
                sql = sql.format(",".join(map(str, inmembers_alive)))
            rows = yield util.whdb.runQuery(
                sql
                ,(userid, )
            )
            cards = [{"id":row[0], "level":row[1], "exp":row[2], "proto":row[3]
                ,"attrs":[row[4], row[5], row[6], row[7], row[8]]
                ,"hpCrystal":row[9], "hpExtra":row[10]} for row in rows]

            for i, card in enumerate(cards):
                if warlord == card["id"]:
                    warlord_card = card
                    if is_warlord_appended:
                        del cards[i]
                        break

            # levelup
            exp_per_card = int(exp / live_num)
            if warlord_card["level"] < 20:
                exp_per_card *= 2

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
                        next_lv_exp = int(lvtbl.get(level+1, "exp"))

                    #max level check
                    if level >= max_level:
                        level = max_level
                        card["exp"] = int(lvtbl.get(level, "exp"))

                    #level up
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
                        levelup.update(dict(zip(["hp", "atk", "def", "wis", "agi"], card["attrs"])))
                        levelups.append(levelup)
                        if card["id"] == warlord:
                            ap = max_ap

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

            # event
            events = cache["events"]
            eventid = events.get(poskey)
            evt_cards = []
            evt_items = []
            if eventid:
                itemid1, itemnum1, itemid2, itemnum2, itemid3, itemnum3, cardid1, cardid2, cardid3 = \
                    evt_tbl.gets(eventid, "item1ID", "amount1", "item2ID", "amount2", "item3ID", "amount3", "card1ID", "card2ID", "card3ID")
                
                evt_items = [{"id":int(itemid1), "num":int(itemnum1)}, {"id":int(itemid2), "num":int(itemnum2)}, {"id":int(itemid3), "num":int(itemnum3)}]
                evt_cards = [int(cardid1), int(cardid2), int(cardid3)]
                evt_items = [item for item in evt_items if item["id"]]
                evt_cards = [card for card in evt_cards if card]

            # add items
            items_add = []
            money_add = 0
            red_case_add = 0
            gold_case_add = 0
            for item in evt_items:
                itemid = item["id"]
                itemnum = item["num"]
                if itemid == MONEY_BAG_SMALL_ID:
                    n = getMoneyNum(MONEY_BAG_SMALL_ID)
                    money_add += n
                elif itemid == MONEY_BAG_BIG_ID:
                    n = getMoneyNum(MONEY_BAG_BIG_ID)
                    money_add += n
                elif itemid == RED_CASE_ID:
                    cache["redCase"] += itemnum
                    red_case_add += itemnum
                    continue
                elif itemid == GOLD_CASE_ID:
                    cache["goldCase"] += itemnum
                    gold_case_add += itemnum
                    continue
                else:
                    if itemid in items:
                        items[itemid] += itemnum
                    else:
                        items[itemid] = itemnum
                items_add.append(item)

            # add cards
            if evt_cards:
                evt_cards = yield create_cards(userid, evt_cards, max_card_num, 1)

            # delete events
            if poskey in cache["events"]:
                del cache["events"][poskey]

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
                """UPDATE playerInfos SET zoneCache=%s, ap=%s, items=%s
                        WHERE userId=%s"""
                ,(json.dumps(cache), ap, json.dumps(items), userid)
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
            reply["items"] = evt_items
            reply["cards"] = evt_cards
            reply["currPos"] = dict(zip(["x", "y"], currpos))
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()


class CatchMonster(tornado.web.RequestHandler):
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
                """ SELECT zoneCache, items, maxCardNum FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            cache = json.loads(row[0])
            items = json.loads(row[1])
            items = {int(k):v for k, v in items.iteritems()}
            max_card_num = row[2]

            band = cache["band"]
            members = band["members"]

            # post input
            input = json.loads(self.request.body)
            catch_item = input["catchItem"]

            # catch
            ADV_POWDER = 5
            POWDER = 6
            catched_mons = []
            if catch_item in [ADV_POWDER, POWDER]:
                item_num = items.get(catch_item, 0)
                if item_num == 0:
                    raise Exception("not enough item")
                items[catch_item] -= 1
                catch_mons = cache.get("catchMons")
                if catch_mons:
                    probs = {1:0.5, 2:0.3, 3:0.2, 4:0.1}
                    for mon in catch_mons:
                        rarity = mon_card_tbl.get(mon, "rarity")
                        prob = probs.get(rarity, 0)
                        if random() < prob or catch_item == ADV_POWDER:
                            catched_mons.append(mon)

                    if catched_mons:
                        catched_mons = yield create_cards(userid, catched_mons, max_card_num, 1)

                    del cache["catchMons"]


            ## update band infos in zoneCache
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s, items=%s
                        WHERE userId=%s"""
                ,(json.dumps(cache), json.dumps(items), userid)
            )

            # reply
            reply = util.new_reply()
            reply["catchedMons"] = catched_mons
            reply["powder"] = items.get(POWDER, 0)
            reply["advPowder"] = items.get(ADV_POWDER, 0)
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
                """ SELECT zoneCache, items, lastZoneId, maxCardNum, maxTradeNum, lastFormation, money, bands FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            if not row[0]:
                raise Exception("not in zone")
            cache = json.loads(row[0])
            items = json.loads(row[1])
            items = {int(k):v for k, v in items.iteritems()}
            last_zoneid = row[2]
            max_card_num = row[3]
            max_trade_num = row[4]
            last_formation = row[5]
            money = row[6]
            bands = json.loads(row[7])

            if cache["currPos"] != cache["goalPos"]:
                raise Exception("palyer not at goal pos")

            # open cases
            zoneid = cache["zoneId"]
            maprow = map_tbl.get_row(zoneid)
            
            red_case_items = []
            gold_case_items = []

            # red case
            for x in xrange(cache["redCase"]):
                caseid = int(map_tbl.get_value(maprow, "treasureprobabilityID"))
                itemid = int(case_tbl.get_item(caseid))
                itemobj = {"id":itemid}
                if itemid in (MONEY_BAG_SMALL_ID, MONEY_BAG_BIG_ID):
                    n = getMoneyNum(itemid)
                    itemobj["num"] = n
                    money += n
                else:
                    itemobj["num"] = 1
                    if itemid in items:
                        items[itemid] += 1
                    else:
                        items[itemid] = 1
                red_case_items.append(itemobj)

            # gold case
            for x in xrange(cache["goldCase"]):
                caseid = int(map_tbl.get_value(maprow, "chestprobabilityID"))
                itemid = int(case_tbl.get_item(caseid))
                itemobj = {"id":itemid}
                if itemid in (MONEY_BAG_SMALL_ID, MONEY_BAG_BIG_ID):
                    n = getMoneyNum(itemid)
                    itemobj["num"] = n
                    money += n
                else:
                    itemobj["num"] = 1
                    if itemid in items:
                        items[itemid] += 1
                    else:
                        items[itemid] = 1
                gold_case_items.append(itemobj)

            # if first time complete
            new_last_zone_id = None
            new_max_card_num = None
            new_max_trade_num = None
            new_last_formation = None
            rwditems = []
            rwdcards = []

            if last_zoneid == zoneid:
                # find new zone id
                num = int(zone_tbl.get(zoneid, "nextZoneId"))
                if num and num > last_zoneid:
                    new_last_zone_id = last_zoneid = num

                # reward event
                evtid = map_tbl.get_value(maprow, "rewardeventID")
                evtrow = evt_tbl.get_row(evtid)

                ## reward items
                for i in xrange(3):
                    itemid = int(evt_tbl.get_value(evtrow, "item%dID"%(i+1)))
                    itemnum = int(evt_tbl.get_value(evtrow, "amount%d"%(i+1)))
                    if itemid and itemnum:
                        if itemid in (MONEY_BAG_SMALL_ID, MONEY_BAG_BIG_ID):
                            itemnum = getMoneyNum(itemid) * itemnum
                            money += itemnum
                        else:
                            if itemid in items:
                                items[itemid] += itemnum
                            else:
                                items[itemid] = itemnum
                        rwditems.append({"id": itemid, "num":itemnum})

                ## reward cards
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
                    mem_num1 = int(fmt_tbl.get(last_formation, "maxNum"))
                    mem_num2 = int(fmt_tbl.get(num, "maxNum"))
                    new_last_formation = last_formation = num
                    if mem_num1 != mem_num2:
                        if mem_num2 - mem_num1 != 1:
                            raise Exception("new formation member count error:%d->%d")
                        for band in bands:
                            mem_num = mem_num2
                            members = band["members"]
                            n = len(members)
                            front = members[:(n/2)]
                            back = members[(n/2):-1]

                            lfront = len(front)
                            if lfront < mem_num:
                                front += (mem_num - lfront)*[None]
                            elif lfront > mem_num:
                                front = front[:mem_num]

                            lback = len(back)
                            if lback < mem_num:
                                back += (mem_num - lback)*[None]
                            elif lback > mem_num:
                                back = back[:mem_num]

                            band["members"] = front + back
                            band["formation"] = new_last_formation

            # db store
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=NULL, inZoneId=0, items=%s, lastZoneId=%s
                    , maxCardNum=%s, maxTradeNum=%s, lastFormation=%s, money=%s, bands=%s
                    WHERE userid=%s"""
                ,(json.dumps(items), last_zoneid, max_card_num, max_trade_num, last_formation, money, json.dumps(bands), session["userid"])
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
    (r"/whapi/zone/catchmonster", CatchMonster),
    (r"/whapi/zone/complete", Complete),
]

map_tbl = util.CsvTbl("data/maps.csv", "zoneID")
plc_tbl = PlacementTbl()
mongrp_tbl = util.CsvTbl("data/monsters.csv", "ID")
case_tbl = CaseTbl()
zone_tbl = util.CsvTbl("data/zones.csv", "id")
mon_card_tbl = util.CsvTbl("data/monstercards.csv", "ID")
evt_tbl = util.CsvTbl("data/events.csv", "ID")
map_evt_tbl = util.CsvTblMulKey("data/mapevents.csv", "mapid", "tilevalue")
