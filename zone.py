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

BLANK_ALL = 4       # tile index in tiled(the editor), gen item or monster
BLANK_ITEM = 5      # tile index which generate item only
BLANK_MON = 6       # tile index which generate monster only

class MapTbl(object):
    def __init__(self):
        self.header = {}
        self.body = {}
        csvpath = "data/map/map.csv"
        with open(csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True;
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    for colname in row:
                        if i != 0:
                            self.header[colname] = i - 1
                        i = i + 1
                else:
                    self.body[row[0]] = row[1:]

    def getZone(self, zoneid):
        return self.body[zoneid]

    def getValue(self, zone, colname):
        return zone[self.header[colname]]

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
    zone = map_tbl.getZone(zoneid)
    itemrate = float(map_tbl.getValue(zone, "item%"))
    monsterrate = float(map_tbl.getValue(zone, "monster%"))
    eventrate = float(map_tbl.getValue(zone, "event%"))

    nonerate = 1.0 - itemrate - monsterrate - eventrate
    if nonerate < 0:
        raise ValueError("sum of percent greater than 1");

    rand1all = WeightedRandom(nonerate, itemrate, monsterrate, eventrate)
    rand1item = WeightedRandom(nonerate, itemrate + monsterrate, 0, eventrate)
    rand1mon = WeightedRandom(nonerate, 0, itemrate + monsterrate, eventrate)

    woodrate = float(map_tbl.getValue(zone, "wood%"))
    treasurerate = float(map_tbl.getValue(zone, "treasure%"))
    chestrate = float(map_tbl.getValue(zone, "chest%"))
    littlegoldrate = float(map_tbl.getValue(zone, "littlegold%"))
    biggoldrate = float(map_tbl.getValue(zone, "biggold%"))
    nonerate = 1.0 - woodrate - treasurerate - chestrate - littlegoldrate - biggoldrate
    if nonerate < -0.0001:
        raise ValueError("sum of percent greater than 1: nonerate = %s" % nonerate);

    rand2item = WeightedRandom(nonerate, woodrate, treasurerate, chestrate, littlegoldrate, biggoldrate)

    mongrpids = []
    for i in xrange(1, 11):
        monid = int(map_tbl.getValue(zone, "monster%dID" % i))
        if monid:
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
                out[k] = grpid+10000
            elif r == 3:    # event
                out[k] = -2

    return out

# =============================================
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

            #param
            try:
                zongid = self.get_argument("zoneid")
            except:
                send_error(self, err_param)
                return;

            #
            out = genPlacements(zongid)
            self.write(out)
        
        except:
            send_internal_error(self)
        finally:
            self.finish()


handlers = [
    (r"/whapi/zone/get", Get),
]

map_tbl = MapTbl()
plc_tbl = PlacementTbl()

# =============================================
if __name__ == "__main__":
    out = genPlacements("50101")
    print out