from error import *
from session import *
import g
import util

import tornado.web
import adisp
import brukva
import simplejson as json
import csv
import logging
import os
from datetime import datetime, timedelta
import logging
from random import random, choice

import tornadoredis
import tornado.gen



TILE_ALL = 4        # tile index in tiled(the editor), gen item or monster
TILE_ITEM = 5       # tile index which generate item only
TILE_MON = 6        # tile index which generate monster only
TILE_START = 2      # start tile
TILE_GOAL = 3       # goal tile

class CsvTbl(object):
    def __init__(self, csvpath, keycol):
        self.header = {}    # {colName:colIndex}
        self.body = {}
        with open(csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True
            keycolidx = None
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    for colname in row:
                        if colname == keycol:
                            keycolidx = i
                        self.header[colname] = i
                        i += 1
                    if keycolidx == None:
                        raise ValueError("key column not found:" + keycol)
                else:
                    self.body[row[keycolidx]] = row

    def get_row(self, key):
        return self.body[key]

    def get_value(self, row, colname):
        return row[self.header[colname]]

    def get(self, rowkey, colname):
        return self.body[rowkey][self.header[colname]]


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
        cvs_case = CsvTbl("data/case.csv", "ID")
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
                "redCase":0, "goldenCase":0, "monGrpId":-1}
    return cache

# =============================================
def trans_cache_to_client(cache):
    out = cache
    objs = cache["objs"]
    outobjs = []
    for k, v in objs.iteritems():
        elem = k.split(",")
        elem = map(int, elem)
        #battle
        if v < 0:
            row = mongrp_tbl.get_row(str(-v))
            img = mongrp_tbl.get_value(row, "image")
            v = -int(img)
        elem.append(v)
        outobjs.append(elem)
    out["objs"] = outobjs
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
            # param
            try:
                zoneid = self.get_argument("zoneid")
                bandidx = self.get_argument("bandidx")
            except:
                send_error(self, err_param)
                return
            # gen
            try:
                cache = gen_cache(zoneid)
            except:
                send_error(self, err_not_exist)

            #band


            cachejs = json.dumps(cache)
            startpos = cache["startPos"] 

            # # redis store
            # key = str(session["userid"])+"/zonecache"
            # yield g.redis().delete(key)
            # rv = yield g.redis().hmset(key, cache)
            # if not rv:
            #     send_error(self, err_redis)
            #     return

            # db store
            try:
                row_nums = yield g.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s
                            WHERE userid=%s"""
                    ,(cachejs, session["userid"])
                )
            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return

            # response
            clientCache = trans_cache_to_client(cache)
            clientCache["error"] = no_error
            rspJs = json.dumps(clientCache)
            self.write(rspJs)
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
                    """UPDATE playerInfos SET zoneCache=NULL
                            WHERE userid=%s"""
                    ,(session["userid"],)
                )
            except Exception as e:
                logging.debug(e)
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
            except Exception as e:
                logging.debug(e)
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

            # param
            path = []
            try:
                itpath = iter(json.loads(self.request.body))
                try:
                    lastPoint = None
                    while True:
                        x = itpath.next()
                        y = itpath.next()
                        if lastPoint and (abs(lastPoint[0]-x) + abs(lastPoint[1]-y) != 3):
                            raise Exception("dist not 3")
                        lastPoint = (x, y)
                        path.append(lastPoint)
                except StopIteration:
                    pass
                except:
                    raise
                
                if len(path) < 2:
                    raise Exception("path too short")

            except:
                send_error(self, err_post)
                return

            # db get cache
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT zoneCache, ap, maxAp, lastApTime, UTC_TIMESTAMP(), items, gold FROM playerInfos 
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
                gold = row[6]

                if not last_ap_time:
                    last_ap_time = datetime(2013, 1, 1)

                if not items:
                    items = {}
                else:
                    items = json.loads(items)

                if not cache:
                    send_error(self, "err_no_cache")
                    return
                else:
                    cache = json.loads(cache)

            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return

            

            # check path
            try:
                #check start pos
                currpos = cache["currPos"]
                currpos = (currpos["x"], currpos["y"])
                if currpos != path[0]:
                    raise Exception("begin coord not match")

                #update ap
                print "curr_time:", curr_time
                print "last_ap_time:", last_ap_time
                dt = curr_time - last_ap_time
                dt = int(dt.total_seconds())
                print "dt:", dt
                ap_add_duration = 10
                dap = dt // ap_add_duration
                print "dap:", dap
                if dap:
                    ap = min(max_ap, ap + dap)
                if ap == max_ap:
                    last_ap_time = curr_time
                else:
                    last_ap_time = curr_time - timedelta(seconds = dt % ap_add_duration)

                if ap == 0:
                    send_error(self, "no_ap")
                    return

                path = path[1:]
                print "path:", path, "ap:", ap
                if len(path) > ap:
                    path = path[:ap]

                ap -= len(path)
                print "ap:", ap
            except:
                send_error(self, err_post)
                return

            # check event exist
            currpos = path[-1]
            poskey = "%d,%d" % (currpos[0], currpos[1])
            evtid = cache["objs"].get(poskey)
            item_updated = False
            if evtid:
                del cache["objs"][poskey]
                zoneid = cache["zoneId"]
                maprow = map_tbl.get_row(zoneid)
                if evtid == 10000:      # event
                    pass
                elif evtid < 0:         # battle
                    cache["monGrpId"] = -evtid
                    monrow = mongrp_tbl.get_row(str(-evtid))
                    # img = mongrp_tbl.get_value(monrow, "image")
                    # fixme
                elif evtid == 1:    # wood case
                    caseid = map_tbl.get_value(maprow, "woodprobabilityID")
                    itemid = case_tbl.get_item(caseid)
                    item_updated = True
                elif evtid == 2:    # red case
                    cache["redCase"] += 1
                elif evtid == 3:    # golden case
                    cache["goldenCase"] += 1
                elif evtid == 4:
                    gold += 100
                elif evtid == 5:
                    gold += 1000
            
            # update
            cache["currPos"] = {"x":currpos[0], "y":currpos[1]}
            cachejs = json.dumps(cache)
            try:
                if item_updated:
                    itemjs = json.dumps(item)
                    yield g.whdb.runOperation(
                        """UPDATE playerInfos SET zoneCache=%s, ap=%s, lastApTime=%s,
                            gold=%s, items=%s
                                WHERE userid=%s"""
                        ,(cachejs, ap, last_ap_time, gold, itemjs, session["userid"])
                    )
                else:
                    yield g.whdb.runOperation(
                        """UPDATE playerInfos SET zoneCache=%s, ap=%s, lastApTime=%s,
                            gold=%s
                                WHERE userid=%s"""
                        ,(cachejs, ap, last_ap_time, gold, session["userid"])
                    )
            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return

            # response
            self.write(poskey)

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/zone/enter", Enter),
    (r"/whapi/zone/withdraw", Withdraw),
    (r"/whapi/zone/get", Get),
    (r"/whapi/zone/move", Move),
]

map_tbl = CsvTbl("data/map.csv", "zoneID")
plc_tbl = PlacementTbl()
mongrp_tbl = CsvTbl("data/monster.csv", "ID")
case_tbl = CaseTbl()

# =============================================
if __name__ == "__main__":
    out = gen_cache("50101")
    print out