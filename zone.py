from error import *
from session import *
import g
import tornado.web
import adisp
import brukva
import simplejson as json
import csv
import logging
from random import random

header = {}     # csv
body = {}       # csv
placements = {}     # jsons export from tiled(editor)

def load():
    load_csv()
    load_event("data/map/50101.json")

def load_csv():
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
                        header[colname] = i - 1
                    i = i + 1
            else:
                body[row[0]] = row[1:]

def load_event(filepath):
    zongid = filepath.split('/')[-1].split('.')[0]
    with open(filepath) as f:
        root = json.load(f)

        layers = root["layers"]
        width = root["width"]
        height = root["height"]
        zone = {"width":width, "height":height}
        for layer in layers:
            if layer["name"] == "event":
                zone["objs"] = parse_placement(layer["data"], width, height)

        placements[zongid] = zone

def parse_placement(data, width, height):
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

class WeightedRandom(object):
    def __init__(self, *weights):
        sum = 0
        uppers = []
        for weight in weights:
            sum += weight
            uppers.append(sum)
        self.uppers = [x/float(sum) for x in uppers]
        print self.uppers

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
    objs = placements[zoneid].objs
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
            genPlacements()
        
        except:
            send_internal_error(self)
        finally:
            self.finish()


handlers = [
    (r"/whapi/zone/get", Get),
]

# =============================================
if __name__ == "__main__":
    load()