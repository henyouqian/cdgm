import util
import logging
import urllib2
import os
import json

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


plc_tbl = PlacementTbl()
case_tbl = CaseTbl()

card_tbl = util.CsvTbl("data/cards.csv", "ID")
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


tables = [card_tbl, grow_tbl, evo_tbl, evo_cost_tbl, skill_tbl, skill_level_tbl, warlord_level_tbl, card_level_tbl, 
    map_tbl, mongrp_tbl, zone_tbl, mon_card_tbl, evt_tbl, map_evt_tbl, fmt_tbl, pvp_match_tbl, pvp_test_data_tbl]


def csv_reload():
    for tbl in tables:
        tbl.reload()

    global plc_tbl, case_tbl
    plc_tbl = PlacementTbl()
    case_tbl = CaseTbl()

    global pvp_win_reward_tbl
    pvp_win_reward_tbl = PvpWinRewardTbl()

    logging.info("csv reloaded.")

def send_reload(host, port):
    f = urllib2.urlopen("http://%s:%s/internal/reloadCsv"%(host, port))
    f.close()

