from error import *
from session import *
import g
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

BLANK_ALL = 4       # tile index in tiled(the editor), gen item or monster
BLANK_ITEM = 5      # tile index which generate item only
BLANK_MON = 6       # tile index which generate monster only

class CsvTbl(object):
    def __init__(self, csvpath, keycol):
        self.header = {}
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
                    zongid = nameext[0]
                    with open(path, "rb") as f:
                        root = json.load(f)

                        layers = root["layers"]
                        width = root["width"]
                        height = root["height"]
                        zone = {"width":width, "height":height}
                        for layer in layers:
                            if layer["name"] == "event":
                                zone["placements"] = self._parse_placement_conf(layer["data"], width, height)

                        self.placements[zongid] = zone
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

class MonGrpTbl(object):
    def __init__(self):
        self.header = {}
        self.body = {}
        csvpath = "data/monster.csv"
        with open(csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True;
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    row = row[1:]
                    for colname in row:
                        self.header[colname] = i
                        i += 1
                else:
                    self.body[row[0]] = row[1:]

    def getRow(self, key):
        return self.body[key]

    def getValue(self, row, colname):
        return row[self.header[colname]]


class WeightedRandom(object):
    def __init__(self, *weights):
        sum = 0
        uppers = []
        for weight in weights:
            sum += weight
            uppers.append(sum)
        self.uppers = [x/float(sum) for x in uppers]

    def get(self):
        rdm = random();
        idx = 0
        for upper in self.uppers:
            if rdm <= upper:
                return idx
            idx += 1
        return idx-1

def genPlacements(zoneid):
    out = {}
    plcs = plc_tbl.getZoneData(zoneid)
    maprow = map_tbl.getRow(zoneid)
    itemrate = float(map_tbl.getValue(maprow, "item%"))
    monsterrate = float(map_tbl.getValue(maprow, "monster%"))
    eventrate = float(map_tbl.getValue(maprow, "event%"))

    nonerate = 1.0 - itemrate - monsterrate - eventrate
    if nonerate < 0:
        raise ValueError("sum of percent greater than 1");

    rand1all = WeightedRandom(nonerate, itemrate, monsterrate, eventrate)
    rand1item = WeightedRandom(nonerate, itemrate + monsterrate, 0, eventrate)
    rand1mon = WeightedRandom(nonerate, 0, itemrate + monsterrate, eventrate)

    woodrate = float(map_tbl.getValue(maprow, "wood%"))
    treasurerate = float(map_tbl.getValue(maprow, "treasure%"))
    chestrate = float(map_tbl.getValue(maprow, "chest%"))
    littlegoldrate = float(map_tbl.getValue(maprow, "littlegold%"))
    biggoldrate = float(map_tbl.getValue(maprow, "biggold%"))
    nonerate = 1.0 - woodrate - treasurerate - chestrate - littlegoldrate - biggoldrate
    if nonerate < -0.0001:
        raise ValueError("sum of percent greater than 1: nonerate = %s" % nonerate);

    rand2item = WeightedRandom(nonerate, woodrate, treasurerate, chestrate, littlegoldrate, biggoldrate)

    mongrpids = []
    for i in xrange(1, 11):
        monid = map_tbl.getValue(maprow, "monster%dID" % i)
        if monid != "0":
            mongrpids.append(monid)
        else:
            break

    for k, v in plcs.items():
        if v in (BLANK_ALL, BLANK_ITEM, BLANK_MON):
            if v == BLANK_ALL:
                r = rand1all.get();
            elif v == BLANK_ITEM:
                r = rand1item.get();
            elif v == BLANK_MON:
                r = rand1mon.get();

            if r == 1:      # item
                itemtype = rand2item.get()
                if itemtype:
                    out[k] = itemtype
            elif r == 2:    # monster
                grpid = choice(mongrpids)
                # row = mongrp_tbl.getRow(grpid)
                # img = mongrp_tbl.getValue(row, "image")
                # out[k] = -int(img)
                out[k] = -int(grpid)
            elif r == 3:    # event
                out[k] = 10000

    return out

# =============================================
def transCacheFormat(cache):
    out = []
    for k, v in cache.iteritems():
        elem = k.split(",")
        elem = map(lambda x:int(x), elem)
        elem.append(v)
        out.append(elem)
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
                zongid = self.get_argument("zoneid")
            except:
                send_error(self, err_param)
                return;

            # gen
            try:
                cache = genPlacements(zongid)
                rsp = transCacheFormat(cache)
            except:
                send_error(self, err_not_exist)

            cache = json.dumps(cache)
            rsp = json.dumps(rsp)

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
                    ,(cache, session["userid"])
                )
            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return;

            # response
            self.write(rsp)

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


            # # redis get
            # key = str(session["userid"])+"/zonecache"
            # rv = yield g.redis().hgetall(key)
            # if not rv:
            #     send_error(self, err_redis)
            #     return;
            # else:
            #     rsp = []
            #     for k, v in rv.iteritems():
            #         elem = k.split(",")
            #         elem.append(v)
            #         elem = map(lambda x:int(x), elem)
            #         rsp.append(elem)
            #     js = json.dumps(rsp)
            #     self.write(js)

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
            rsp = transCacheFormat(cache)
            rsp = json.dumps(rsp)
            self.write(rsp)

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

            # check event exist
            cache = json.loads(cache)
            evtid = cache.get("%d,%d" % (x, y))
            if not evtid:
                send_error(self, err_key)
                return;

            # 
            if evtid == 10000:  # event
                pass
            elif evtid < 0:
                pass
            else:
                pass
            self.write("xxxx")

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

# =============================================
if __name__ == "__main__":
    out = genPlacements("50101")
    print out