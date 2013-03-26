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
            firstrow = True;
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

    def getRow(self, key):
        return self.body[key]

    def getValue(self, row, colname):
        return row[self.header[colname]]


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

    def getZoneData(self, zoneid):
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

    def getItem(self, caseId):
        try:
            indices, weights = self._t[caseId]
            rdm = WeightedRandom(1.0, *weights)
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
        rdm = random();
        idx = 0
        for upper in self.uppers:
            if rdm <= upper:
                return idx
            idx += 1
        return -1

def genCache(zoneid):
    tiles = plc_tbl.getZoneData(zoneid)
    maprow = map_tbl.getRow(zoneid)
    itemrate = float(map_tbl.getValue(maprow, "item%"))
    monsterrate = float(map_tbl.getValue(maprow, "monster%"))
    eventrate = float(map_tbl.getValue(maprow, "event%"))

    rand1all = WeightedRandom(1.0, itemrate, monsterrate, eventrate)
    rand1item = WeightedRandom(1.0, itemrate + monsterrate, 0, eventrate)
    rand1mon = WeightedRandom(1.0, 0, itemrate + monsterrate, eventrate)

    woodrate = float(map_tbl.getValue(maprow, "wood%"))
    treasurerate = float(map_tbl.getValue(maprow, "treasure%"))
    chestrate = float(map_tbl.getValue(maprow, "chest%"))
    littlegoldrate = float(map_tbl.getValue(maprow, "littlegold%"))
    biggoldrate = float(map_tbl.getValue(maprow, "biggold%"))

    rand2item = WeightedRandom(1.0, woodrate, treasurerate, chestrate, littlegoldrate, biggoldrate)

    mongrpids = []
    for i in xrange(1, 11):
        monid = map_tbl.getValue(maprow, "monster%dID" % i)
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
            r = rand1all.get();
        elif v == TILE_ITEM:
            r = rand1item.get();
        elif v == TILE_MON:
            r = rand1mon.get();
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
            # row = mongrp_tbl.getRow(grpid)
            # img = mongrp_tbl.getValue(row, "image")
            # objs[k] = -int(img)
            objs[k] = -int(grpid)
        elif r == 2:    # event
            objs[k] = 10000


    cache = {"zoneId":int(zoneid), "objs":objs, "startPos":startpos, "goalPos":goalpos, "currPos":startpos}
    return cache

# =============================================
def transCacheToClient(cache):
    out = cache
    objs = cache["objs"]
    outobjs = []
    for k, v in objs.iteritems():
        elem = k.split(",")
        elem = map(int, elem)
        #battle
        if v < 0:
            row = mongrp_tbl.getRow(str(-v))
            img = mongrp_tbl.getValue(row, "image")
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
            except:
                send_error(self, err_param)
                return;
            # gen
            try:
                cache = genCache(zoneid)
            except:
                send_error(self, err_not_exist)

            cacheJs = json.dumps(cache)
            startpos = cache["startPos"] 

            # # redis store
            # key = str(session["userid"])+"/zonecache"
            # yield g.redis().delete(key)
            # rv = yield g.redis().hmset(key, cache)
            # if not rv:
            #     send_error(self, err_redis)
            #     return;

            # db store
            try:
                row_nums = yield g.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s
                            WHERE userid=%s"""
                    ,(cacheJs, session["userid"])
                )
            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return;

            # response
            clientCache = transCacheToClient(cache)
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
                return;

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
            clientCache = transCacheToClient(cache)
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
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return

            # param
            try:
                x = self.get_argument("x")
                y = self.get_argument("y")
            except:
                send_error(self, err_param)
                return;

            # db get cache
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
                return;

            cache = json.loads(cache)
            lastpos = cache["currPos"]

            # check event exist
            poskey = "%d,%d" % (int(x), int(y))
            evtid = cache["objs"].get(poskey)
            if not evtid:
                send_error(self, err_key)
                return;

            # 
            if evtid == 10000:  # event
                pass
            elif evtid < 0:     # battle
                pass
            else:               # item
                pass

            # update
            cache["currPos"] = {"x":x, "y":y}
            del cache["objs"][poskey]
            cacheJs = json.dumps(cache)
            try:
                row_nums = yield g.whdb.runOperation(
                    """UPDATE playerInfos SET zoneCache=%s
                            WHERE userid=%s"""
                    ,(cacheJs, session["userid"])
                )
            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return;

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
    out = genCache("50101")
    print out