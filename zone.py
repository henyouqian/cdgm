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
                row = mongrp_tbl.getRow(grpid)
                img = mongrp_tbl.getValue(row, "image")
                out[k] = -int(img)
            elif r == 3:    # event
                out[k] = 10000

    return out

# =============================================
class Create(tornado.web.RequestHandler):
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
                out = genPlacements(zongid)
                rsp = []
                for k, v in out.iteritems():
                    elem = k.split(",")
                    elem = map(lambda x:int(x), elem)
                    elem.append(v)
                    rsp.append(elem)
                js = json.dumps(rsp)
                self.write(js)
            except:
                send_error(self, err_not_exist)

            # redis store
            key = str(session["userid"])+"/zonecache"
            yield g.redis().delete(key)
            rv = yield g.redis().hmset(key, out)
            if not rv:
                send_error(self, err_redis)
                return;

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

            # param
            try:
                zongid = self.get_argument("zoneid")
            except:
                send_error(self, err_param)
                return;

            # redis get
            key = str(session["userid"])+"/zonecache"
            rv = yield g.redis().hgetall(key)
            if not rv:
                send_error(self, err_redis)
                return;
            else:
                rsp = []
                for k, v in rv.iteritems():
                    elem = k.split(",")
                    elem.append(v)
                    elem = map(lambda x:int(x), elem)
                    rsp.append(elem)
                js = json.dumps(rsp)
                self.write(js)

        except:
            send_internal_error(self)
        finally:
            self.finish()




class Redis(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # redis store
            # key = "redistest"
            # out = {"35,19": 1, "14,28": -2, "14,25": -1, "14,22": -2, "32,28": -2, "41,16": -2, "35,22": -2, "35,25": -2, "26,25": -2, "23,37": -1, "26,22": 1, "26,28": -2, "14,19": 4, "35,28": -2, "14,31": 10000, "38,16": -1, "35,16": -2, "17,37": 5, "17,19": -2, "26,31": -2, "26,34": 4, "26,37": -2}
            # rv = yield g.redis().set(key, "b"*10)
            # if not rv:
            #     send_error(self, err_redis)
            #     return;
           
            rv = yield g.redis().hget('redistest', "a")
            # rv = yield g.redis().randomkey()
            self.write(rv)

        except:
            send_internal_error(self)
        finally:
            self.finish()

class RedisSet(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # redis store
            key = "redistest"
            out = {"35,19": 1, "14,28": -2, "14,25": -1, "14,22": -2, "32,28": -2, "41,16": -2, "35,22": -2, "35,25": -2, "26,25": -2, "23,37": -1, "26,22": 1, "26,28": -2, "14,19": 4, "35,28": -2, "14,31": 10000, "38,16": -1, "35,16": -2, "17,37": 5, "17,19": -2, "26,31": -2, "26,34": 4, "26,37": -2}
            rv = yield g.redis().hset(key, "a", "b"*100000)
            # if not rv:
            #     send_error(self, err_redis)
            #     return;
           
            # rv = yield g.redis().get('redistest')
            # rv = yield g.redis().randomkey()
            self.write("ok")

        except:
            send_internal_error(self)
        finally:
            self.finish()

CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=10,
                                              wait_for_available=True)

from tornado.httpclient import AsyncHTTPClient
class Redis2(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    # @tornado.gen.coroutine
    def get(self):
        try:
            c = tornadoredis.Client(connection_pool=CONNECTION_POOL)
            foo = yield tornado.gen.Task(c.hgetall, 'redistest')
            # foo = yield c.hgetall('redistest')

            # http_client = AsyncHTTPClient()
            # response = yield http_client.fetch("http://weibo.com")
            # response = yield tornado.gen.Task(http_client.fetch, "http://weibo.com")
            self.write(foo)

        except:
            send_internal_error(self)
        finally:
            self.finish()

import redis
r = redis.Redis("localhost", 6379)
class Redis3(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        try:
            foo = r.get('redistest')
            self.write(foo)

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/zone/create", Create),
    (r"/whapi/zone/get", Get),
    (r"/whapi/redis", Redis),
    (r"/whapi/redisset", RedisSet),
    (r"/whapi/redis2", Redis2),
    (r"/whapi/redis3", Redis3),
]

map_tbl = CsvTbl("data/map.csv", "zoneID")
plc_tbl = PlacementTbl()
mongrp_tbl = CsvTbl("data/monster.csv", "ID")

# =============================================
if __name__ == "__main__":
    out = genPlacements("50101")
    print out