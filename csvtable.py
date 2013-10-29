import util
import logging
import urllib2
import os
import json
import csv
import random

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
        rdm = util.WeightedRandom(0, *weights)
        idx = rdm.get()
        return indices[idx]


class PvpWinRewardTbl(object):
    def __init__(self):
        tbl = util.parse_csv("data/pvpWinRewards.csv")
        self._tbl = {}
        for row in tbl:
            row = {k:int(v) for k, v in row.iteritems()}
            wincount = int(row["winCount"])
            if wincount not in self._tbl:
                self._tbl[wincount] = [row]
            else:
                self._tbl[wincount].append(row)

    def get(self, wincount):
        return self._tbl.get(wincount, None)


class DropsTbl(object):
    def __init__(self):
        tbl = util.parse_csv("data/drops.csv")
        self._tbl = {}
        for row in tbl:
            idv = int(row["id"])
            dropsInfo = {'prob': float(row['prob']), 'amount': int(row['amount']), 'objid': int(row['objid'])}
            if idv in self._tbl:
                self._tbl[idv].append(dropsInfo)
            else:
                self._tbl[idv] = [dropsInfo]

    def drop(self, zoneid):
        zoneDrops = self._tbl.get(int(zoneid))
        if zoneDrops:
            weights = [v['prob'] for v in zoneDrops]
            rand = util.WeightedRandom(1.0, *weights)
            r = rand.get()
            if r == -1:
                return None
            return zoneDrops[r]["objid"]


class PactTable(object):
    def __init__(self, file_path):
        with open(file_path, 'rb') as csvfile:
            rows = csv.reader(csvfile)
            row1 = rows.next();
            head = dict(zip(row1, xrange(len(row1))))
            pacts = {}
            packidIdx = head["pactid"]
            resultIdx = head["result"]
            weightIdx = head["weight"]
            limittimesIdx = head.get("limittimes", -1)
            for row in rows:
                pact_id = row[packidIdx]
                result = row[resultIdx]
                weight = float(row[weightIdx])
                if weight <= 0:
                    continue
                if pact_id in pacts:
                    pacts[pact_id]["results"].append(result)
                    weights = pacts[pact_id]["weights"]
                    weights.append(weight)
                else:
                    pacts[pact_id] = {"results":[result], "weights":[weight]}

                if limittimesIdx != -1:
                    limittimes = int(row[limittimesIdx])
                    if limittimes >= 0:
                        if "limittimeses" in pacts[pact_id]:
                            pacts[pact_id]["limittimeses"].append(limittimes)
                        else:
                            pacts[pact_id]["limittimeses"] = [limittimes]

            self._pacts = pacts


    def random_get(self, pact_id, pact_times_map):
        pact = self._pacts[pact_id]
        weights = pact["weights"]
        results = pact["results"]
        max_weight = 0
        haslimit = "limittimeses" in pact
        if haslimit:
            limittimeses = pact["limittimeses"]
            _weights = []
            _results = []
            _limittimeses = []
            for i in xrange(len(weights)):
                limittimes = limittimeses[i]

                key = "%s/%s" % (pact_id, results[i])
                pacttimes = pact_times_map.get(key, 0)
                if limittimes == 0 or pacttimes < limittimes:
                    weight = weights[i]
                    if not _weights:
                        _weights.append(weight)
                    else:
                        _weights.append(weight + _weights[-1])
                    _results.append(results[i])
                    max_weight += weight

            weights = _weights
            results = _results
        else:
            _weights = []
            for weight in weights:
                max_weight += weight
                if not _weights:
                    _weights.append(weight)
                else:
                    _weights.append(weight + _weights[-1])

            weights = _weights

        rd = random.uniform(0.0, max_weight)
        idx = util.lower_bound(weights, rd)
        if idx < 0:
            idx = -idx - 1;

        if haslimit:
            limittimeses = pact["limittimeses"]
            limittimes = limittimeses[idx]
            changed = False
            if limittimes > 0:
                key = "%s/%s" % (pact_id, results[idx])
                pacttimes = pact_times_map.get(key, 0)
                pact_times_map[key] = pacttimes + 1
                changed = True
            return results[idx], changed
        else:
            return results[idx]


plc_tbl = None
case_tbl = None

card_tbl = None
grow_tbl = None
evo_tbl = None
evo_cost_tbl = None
skill_tbl = None
skill_level_tbl = None
warlord_level_tbl = None
card_level_tbl = None
map_tbl = None
mongrp_tbl = None
zone_tbl = None
mon_card_tbl = None
evt_tbl = None
map_evt_tbl = None
fmt_tbl = None
pvp_match_tbl = None
pvp_test_data_tbl = None
pvp_win_reward_tbl = None
pvp_rank_reward_tbl = None
wagon_desc_tbl = None
drops_tbl = None
inst_zone_tbl = None

pact_tbl = None
sub_pact_tbl = None
pact_cost_tbl = None


def csv_reload():
    global plc_tbl, case_tbl, card_tbl, grow_tbl, evo_tbl, evo_cost_tbl, skill_tbl, skill_level_tbl
    global warlord_level_tbl, card_level_tbl, map_tbl, mongrp_tbl, zone_tbl, mon_card_tbl, evt_tbl
    global map_evt_tbl, fmt_tbl, pvp_match_tbl, pvp_test_data_tbl, pvp_win_reward_tbl
    global pvp_rank_reward_tbl, wagon_desc_tbl, drops_tbl, inst_zone_tbl
    global pact_tbl, sub_pact_tbl, pact_cost_tbl

    plc_tbl = PlacementTbl()
    case_tbl = CaseTbl()

    card_tbl = util.CsvTbl("data/cards.csv", "id")
    grow_tbl = util.CsvTblMulKey("data/cardGrowthMappings.csv", "type", "level")
    evo_tbl = util.CsvTblMulKey("data/cardEvolutions.csv", "masterCardId", "evolverCardId")
    evo_cost_tbl = util.CsvTblMulKey("data/cardEvolutionCosts.csv", "masterCardRarity", "evolverCardRarity")
    skill_tbl = util.CsvTbl("data/skills.csv", "id")
    skill_level_tbl = util.CsvTblMulKey("data/skillLevels.csv", "rarity", "level")
    warlord_level_tbl = util.CsvTbl("data/levels.csv", "level")
    card_level_tbl = util.CsvTbl("data/cardLevels.csv", "level")

    map_tbl = util.CsvTbl("data/maps.csv", "zoneID")
    mongrp_tbl = util.CsvTbl("data/monsters.csv", "ID")
    zone_tbl = util.CsvTbl("data/zones.csv", "id")
    mon_card_tbl = util.CsvTbl("data/monstercards.csv", "ID")
    evt_tbl = util.CsvTbl("data/events.csv", "ID")
    map_evt_tbl = util.CsvTblMulKey("data/mapevents.csv", "mapid", "tilevalue")

    fmt_tbl = util.CsvTbl("data/formations.csv", "id")

    pvp_match_tbl = util.CsvTbl("data/pvpmatch.csv", "id")
    pvp_test_data_tbl = util.CsvTbl("data/pvpTestData.csv", "ID")

    pvp_win_reward_tbl = PvpWinRewardTbl()
    pvp_rank_reward_tbl = util.parse_csv("data/pvpRankRewards.csv")

    wagon_desc_tbl = util.CsvTbl("data/wagonDesc.csv", "id")

    drops_tbl = DropsTbl()

    inst_zone_tbl = util.CsvTbl("data/instanceZones.csv", "zoneId")

    pact_tbl = PactTable("data/pacts.csv")
    sub_pact_tbl = PactTable("data/cardpacts.csv")
    pact_cost_tbl = util.CsvTbl("data/pactcost.csv", "id")


csv_reload()

# for i in xrange(10):
#     print drops_tbl.drop("10101")

def send_reload(host, port):
    f = urllib2.urlopen("http://%s:%s/internal/reloadCsv"%(host, port))
    f.close()

