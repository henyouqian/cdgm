from session import *
from error import *
import util
from wagon import Wagon

import tornado.web
import adisp

import json
from itertools import repeat, imap
from random import randint, uniform
import csv

card_tbl = util.CsvTbl("data/cards.csv", "ID")
grow_tbl = util.CsvTblMulKey("data/cardGrowthMappings.csv", "type", "level")
evo_tbl = util.CsvTblMulKey("data/cardEvolutions.csv", "masterCardId", "evolverCardId")
evo_cost_tbl = util.CsvTblMulKey("data/cardEvolutionCosts.csv", "masterCardRarity", "evolverCardRarity")
skill_tbl = util.CsvTbl("data/skills.csv", "id")
skill_level_tbl = util.CsvTblMulKey("data/skillLevels.csv", "rarity", "level")
warlord_level_tbl = util.CsvTbl("data/levels.csv", "level")
card_level_tbl = util.CsvTbl("data/cardLevels.csv", "level")

# # test
# row = grow_tbl.get_row("1", "11")
# print row
# print grow_tbl.get_value(row, "curve")
# print grow_tbl.get(("1", "3"),"curve")

# row = card_tbl.get_row("1")
# print tuple(card_tbl.get_values(row, "name", "cardtype"))

# for __ in xrange(10000):
#   grow_tbl.get(("1", "11"),"curve")

# calc for hp, atk, def, wis, agi
def calc_card_proto_attr(proto_id, level):
    proto = card_tbl.get_row(str(proto_id))
    min_attrs = card_tbl.get_values(proto, 
        "basehp", "baseatk", "basedef", "basewis", "baseagi")
    max_attrs = card_tbl.get_values(proto, 
        "maxhp", "maxatk", "maxdef", "maxwis", "maxagi")
    maxlevel, growtype = card_tbl.get_values(proto, "maxlevel", "growtype")
    if level > int(maxlevel):
        raise ValueError("card proto: level > maxlevel. proto_id=%s"%proto_id)

    growmin = float(grow_tbl.get((growtype, "1"), "curve"))
    growmax = float(grow_tbl.get((growtype, maxlevel), "curve"))
    growcurr = float(grow_tbl.get((growtype, str(level)), "curve"))

    def lerp(min, max, f):
        min = float(min)
        max = float(max)
        return int(min + (max - min)*f)

    f = (growcurr - growmin) / (growmax - growmin)
    return tuple(imap(lerp, min_attrs, max_attrs, repeat(f)))

def is_war_lord(proto_id):
    return 119 <= proto_id <= 226


# @adisp.async
# @adisp.process
# def create(owner_id, proto_id, level, callback):
#     try:
#         hp, atk, _def, wis, agi = calc_card_proto_attr(proto_id, level)
#         skill_1_id, skill_2_id = card_tbl.gets(proto_id, "skillid1", "skillid2")
#         lvtbl = warlord_level_tbl if is_war_lord(proto_id) else card_level_tbl
#         exp = lvtbl.get(level, "exp")
#         card = {"protoId":proto_id, "ownerId":owner_id, "level":level, "exp":exp}
#         card.update({"hp":hp, "atk":atk, "def":_def, "wis":wis, "agi":agi})
#         card.update({"hpCrystal":0, "atkCrystal":0, "defCrystal":0, "wisCrystal":0, "agiCrystal":0})
#         card.update({"hpExtra":0, "atkExtra":0, "defExtra":0, "wisExtra":0, "agiExtra":0})
#         card.update({"skill1Id":skill_1_id, "skill2Id":skill_2_id, "skill2Id":0})
#         card.update({"skill1Level":1, "skill2Level":1, "skill2Level":1})
#         card.update({"skill1Exp":0, "skill2Exp":0, "skill2Exp":0})

#         # fixme: check cards limit and put into wagon
#         conn = yield util.whdb.beginTransaction()
#         try:
#             rows = yield util.whdb.runQuery(
#                 """SELECT COUNT(1) from cardEntities
#                         WHERE ownerId=%s AND inPackage=%s"""
#                 , (owner_id, 1), conn
#             )


#             row_nums = yield util.whdb.runOperation(
#                 """ INSERT INTO cardEntities
#                         ({}) VALUES({})
#                 """.format(",".join(card.keys()), ",".join(("%s",)*len(card)))
#                 , card.values()
#                 , conn
#             )
#             rows = yield util.whdb.runQuery("SELECT LAST_INSERT_ID()", None, conn)
#         finally:
#             yield util.whdb.commitTransaction(conn)

#         if row_nums != 1:
#             raise Exception("db insert error")
#         card["id"] = rows[0][0]

#         callback(card)
#     except Exception as e:
#         callback(e)


@adisp.async
@adisp.process
def create_cards(owner_id, proto_ids, max_card_num, level, callback):
    try:
        cards = []
        for proto_id in proto_ids:
            hp, atk, _def, wis, agi = calc_card_proto_attr(proto_id, level)
            skill_1_id, skill_2_id = card_tbl.gets(proto_id, "skillid1", "skillid2")
            lvtbl = warlord_level_tbl if is_war_lord(proto_id) else card_level_tbl
            exp = lvtbl.get(level, "exp")
            card = {"protoId":proto_id, "ownerId":owner_id, "level":level, "exp":exp}
            card.update({"hp":hp, "atk":atk, "def":_def, "wis":wis, "agi":agi})
            card.update({"hpCrystal":0, "atkCrystal":0, "defCrystal":0, "wisCrystal":0, "agiCrystal":0})
            card.update({"hpExtra":0, "atkExtra":0, "defExtra":0, "wisExtra":0, "agiExtra":0})
            card.update({"skill1Id":skill_1_id, "skill2Id":skill_2_id, "skill2Id":0})
            card.update({"skill1Level":1, "skill2Level":1, "skill2Level":1})
            card.update({"skill1Exp":0, "skill2Exp":0, "skill2Exp":0})
            card.update({"_newInsert":1})
            cards.append(card)

        conn = yield util.whdb.beginTransaction()
        try:
            rows = yield util.whdb.runQuery(
                """SELECT COUNT(1) from cardEntities
                        WHERE ownerId=%s AND inPackage=%s"""
                , (owner_id, 1), conn
            )
            inpack_num = rows[0][0]
            pack_remain_num = max_card_num - inpack_num
            goto_pack_num = min(pack_remain_num, len(cards))
            for idx, card in enumerate(cards):
                if idx < goto_pack_num:
                    card["inPackage"] = 1
                else:
                    card["inPackage"] = 0

            cols = ",".join(cards[0].keys())
            yield util.whdb.runOperationMany(
                """ INSERT INTO cardEntities
                        ({}) VALUES({})
                """.format(cols, ",".join(("%s",)*len(cards[0])))
                , tuple((card.values() for card in cards))
                , conn
            )
            # append key "id" to fetch
            cols += ",id"
            rows = yield util.whdb.runQuery("CALL get_new_cards(%s, %s)", (owner_id, cols), conn)
        finally:
            yield util.whdb.commitTransaction(conn)

        reply = []
        keys = cards[0].keys()
        keys.append("id")
        for row in rows:
            reply.append(dict(zip(keys, row)))
        callback(reply)
    except Exception as e:
        traceback.print_exc()
        callback(e)

class PactTable(object):
    def __init__(self, file_path):
        with open(file_path, 'rb') as csvfile:
            rows = csv.reader(csvfile)
            row1 = rows.next();
            head = dict(zip(row1, xrange(len(row1))))
            pacts = {}
            for row in rows:
                pact_id = row[head["pactid"]]
                result = row[head["result"]]
                weight = row[head["weight"]]
                if weight <= 0:
                    continue
                if pact_id in pacts:
                    pacts[pact_id]["results"].append(row[1])
                    weights = pacts[pact_id]["weights"]
                    weights.append(float(row[2])+weights[-1])
                else:
                    pacts[pact_id] = {"results":[row[1]], "weights":[float(row[2])]}

            self._pacts = pacts

    def random_get(self, pact_id):
        pact = self._pacts[pact_id]
        weights = pact["weights"]
        max_weight = weights[-1]
        rd = uniform(0.0, max_weight)
        idx = util.lower_bound(weights, rd)
        if idx < 0:
            idx = -idx - 1;
        return pact["results"][idx]

pact_tbl = PactTable("data/pacts.csv")
sub_pact_tbl = PactTable("data/cardpacts.csv")
pact_cost_tbl = util.CsvTbl("data/pactcost.csv", "id")


def get_card_from_pact(pact_id):
    sub_pact_id = pact_tbl.random_get(str(pact_id))
    card_id = sub_pact_tbl.random_get(sub_pact_id)
    # print sub_pact_id, card_id
    return card_id

# # test
# for i in xrange(50):
#     get_card_from_pact("1")

# ====================================================
class GetPact(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # param
            try:
                pact_cost_id = int(self.get_argument("packid"))
                num = int(self.get_argument("num"))
                num = min(10, num)
            except:
                send_error(self, err_param)
                return

            # pact cost table
            try:
                pact_id, cost_item_id, cost_num, pact_num = pact_cost_tbl.gets(pact_cost_id, 
                    "pactid", "itemid", "costnum", "pactnum")
                cost_num = int(cost_num)
                pact_num = int(pact_num)

            except:
                raise Exception("get pact cost error: pack_id=%s" % pact_cost_id)

            # get player info
            rows = yield util.whdb.runQuery(
                        """SELECT items, whCoin, maxCardNum, wagonTemp FROM playerInfos
                                WHERE userId=%s"""
                        ,(user_id, )
                    )
            row = rows[0]
            items = json.loads(row[0])
            wh_coin = row[1]
            max_card_num = row[2]
            wagon_temp = Wagon(row[3])

            # check and calc payment
            # only item (include bronze coin and silver coin, not wh coin) can mulitply numbers
            if cost_item_id != 0:
                cost_num *= num
                pact_num *= num

            card_ids = []
            for i in xrange(pact_num):
                card_ids.append(get_card_from_pact(pact_id))

            # wh_coin
            if cost_item_id == 0:
                if wh_coin < cost_num:
                    raise Exception("not enough whcoin:wh_conin=%s < cost_num%s" % (wh_coin, cost_num))
                wh_coin -= cost_num
            # cost items, like bronze or silver coin
            else:
                if (cost_item_id not in items) or (items[cost_item_id] < cost_num):
                    raise Exception("not enough item: cost_item_id=%s, cost_num=%s" % (cost_item_id, cost_num))
                items[cost_item_id] -= cost_num

            # create cards
            cards = yield create_cards(user_id, card_ids, max_card_num, 1)

            # wagon
            for card in cards:
                if not card["inPackage"]:
                    wagon_temp.addCard(card["protoId"], card["id"])

            # real pay and set wagon
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET whCoin=%s, items=%s, wagonTemp=%s
                        WHERE userId=%s"""
                ,(wh_coin, json.dumps(items), json.dumps(wagon_temp.data), user_id )
            )

            # reply
            reply = {"error": no_error}
            reply["cards"] = cards
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class Sell(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # post input
            card_ids = json.loads(self.request.body)
            for card_id in card_ids:
                if not isinstance(card_id, int):
                    raise Exception("card_id must be int")

            # query all cards info and check owner
            rows = yield util.whdb.runQuery(
                """SELECT protoId FROM cardEntities
                        WHERE id IN ({}) AND ownerId = %s""".format(",".join(("%s",)*len(card_ids)))
                ,tuple(card_ids+[user_id])
            )

            proto_ids = [row[0] for row in rows]

            if len(proto_ids) != len(card_ids):
                raise Exception("card id error")

            # query player info
            rows = yield util.whdb.runQuery(
                        """SELECT money, bands, inZoneId, warlord, currentBand FROM playerInfos
                                WHERE userId=%s"""
                        ,(user_id, )
                    )
            row = rows[0]
            money = row[0]
            bands = json.loads(row[1])
            in_zone_id = row[2]
            warlord = row[3]
            current_band = row[4]

            # check whether in current band
            if in_zone_id > 0:
                for card_id in card_ids:
                     if card_id in bands[current_band].members:
                        raise Exception("can not sell card which in current band when in zone")

            if warlord in card_ids:
                raise Exception("warlord can not be sold")

            # add money
            money_add = 0
            for proto_id in proto_ids:
                money_add += int(card_tbl.get(proto_id, "price"))
            
            money += money_add

            # delete if in band
            inband = False
            for band in bands:
                for idx, member in enumerate(band["members"]):
                    if member in card_ids:
                        band[idx] = None
                        inband = True
                        break

            # update playerInfo
            if inband:
                yield util.whdb.runOperation(
                        """UPDATE playerInfos SET money=%s, bands=%s
                                WHERE userId=%s"""
                        ,(money, json.dumps(bands), user_id)
                    )
            else:
                yield util.whdb.runOperation(
                        """UPDATE playerInfos SET money=%s
                                WHERE userId=%s"""
                        ,(money, user_id)
                    )

            # delete card
            yield util.whdb.runOperation(
                "DELETE FROM cardEntities WHERE id IN ({}) AND ownerId = %s".format(",".join(("%s",)*len(card_ids)))
                ,tuple(card_ids+[user_id])
            )

            # reply
            reply = {"error":no_error}
            reply["cardIds"] = card_ids
            reply["moneyAdd"] = money_add
            reply["money"] = money
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Evolution(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # param
            try:
                card_id1 = int(self.get_argument("cardid1"))
                card_id2 = int(self.get_argument("cardid2"))
            except:
                send_error(self, err_param)
                return

            fields_str = """id, protoId, level, exp, 
                            skill1Id, skill1Level, skill1Exp, 
                            skill2Id, skill2Level, skill2Exp, 
                            skill3Id, skill3Level, skill3Exp, 
                            hp, atk, def, wis, agi,
                            hpCrystal, atkCrystal, defCrystal, wisCrystal, agiCrystal,
                            hpExtra, atkExtra, defExtra, wisExtra, agiExtra"""
            fields = fields_str.translate(None, "\n ").split(",")

            # query card info from db and check owner
            rows = yield util.whdb.runQuery(
                """SELECT {}
                        FROM cardEntities
                        WHERE (id=%s OR id=%s) AND ownerId = %s""".format(fields_str)
                ,(card_id1, card_id2, user_id)
            )
            if len(rows) != 2:
                raise Exception("card id error")
            
            cards = [dict(zip(fields, row)) for row in rows]
            # make cards[0] primary
            if cards[0]["id"] == card_id2:
                cards[0], cards[1] = cards[1], cards[0]

            card1, card2 = cards
            
            # spend money
            rarity1 = card_tbl.get(card1["protoId"], "rarity")
            rarity2 = card_tbl.get(card2["protoId"], "rarity")
            cost = int(evo_cost_tbl.get((rarity1, rarity2), "cost"))
            rows = yield util.whdb.runQuery(
                        """SELECT money, bands, isInZone FROM playerInfos
                                WHERE userId=%s"""
                        ,(user_id, )
                    )
            row = rows[0]
            money = row[0]
            bands = json.loads(row[1])
            inZoneId = row[2]
            if inZoneId > 0:
                raise Exception("error in zone")

            if money < cost:
                raise Exception("not enough money")
            money -= cost

            # look up evolution table
            try:
                proto_id = int(evo_tbl.get((str(card1["protoId"]), str(card2["protoId"])), "afterCardId"))
            except:
                raise Exception("card can not do evolution: proto1=%s, proto2=%s" % (card1["protoId"], card2["protoId"]))

            # calc new attr for master card
            card2_max_level = int(card_tbl.get(card2["protoId"], "maxlevel"))
            extra_rate = 0.05
            if card2["level"] == card2_max_level:
                extra_rate = 0.1

            hp_ex = card1["hpExtra"] + int(extra_rate * (card2["hp"] + card2["hpCrystal"] + card2["hpExtra"]))
            atk_ex = card1["atkExtra"] + int(extra_rate * (card2["atk"] + card2["atkCrystal"] + card2["atkExtra"]))
            def_ex = card1["defExtra"] + int(extra_rate * (card2["def"] + card2["defCrystal"] + card2["defExtra"]))
            wis_ex = card1["wisExtra"] + int(extra_rate * (card2["wis"] + card2["wisCrystal"] + card2["wisExtra"]))
            agi_ex = card1["agiExtra"] + int(extra_rate * (card2["agi"] + card2["agiCrystal"] + card2["agiExtra"]))

            hp, atk, _def, wis, agi = calc_card_proto_attr(proto_id, card1["level"])

            card1["protoId"] = proto_id
            card1["hpExtra"] = hp_ex
            card1["atkExtra"] = atk_ex
            card1["defExtra"] = def_ex
            card1["wisExtra"] = wis_ex
            card1["agiExtra"] = agi_ex
            card1["hp"] = hp
            card1["atk"] = atk
            card1["def"] = _def
            card1["wis"] = wis
            card1["agi"] = agi


            yield util.whdb.runOperation(
                    """UPDATE cardEntities SET protoId=%s, hp=%s, atk=%s, def=%s, wis=%s, agi=%s, 
                            hpExtra=%s, atkExtra=%s, defExtra=%s, wisExtra=%s, agiExtra=%s
                            WHERE id=%s"""
                    ,(proto_id, hp, atk, _def, wis, agi, hp_ex, atk_ex, def_ex, wis_ex, agi_ex, card1["id"])
                )

            yield util.whdb.runOperation(
                    """DELETE FROM cardEntities
                            WHERE id=%s"""
                    ,(card2["id"], )
                )
            # del from band if need
            inband = False
            for band in bands:
                for idx, member in enumerate(band["members"]):
                    if member == card2["id"]:
                        band[idx] = None
                        inband = True
                        break
            
            # update playerInfo
            if inband:
                yield util.whdb.runOperation(
                        """UPDATE playerInfos SET money=%s, bands=%s
                                WHERE userId=%s"""
                        ,(money, json.dumps(bands), user_id)
                    )
            else:
                yield util.whdb.runOperation(
                        """UPDATE playerInfos SET money=%s
                                WHERE userId=%s"""
                        ,(money, user_id)
                    )

            # reply
            reply = {"error":no_error}
            reply["money"] = money
            reply["delCardId"] = card2["id"]
            reply["evoCard"] = card1

            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Sacrifice(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # post input
            cards = json.loads(self.request.body)
            card_num = len(cards)
            if card_num < 2 or card_num > 9:
                raise Exception("card_num < 2 or card_num > 9")
            for card in cards:
                if type(card) != int:
                    raise Exception("id must be int")

            # get player info
            rows = yield util.whdb.runQuery(
                """SELECT money, warLord FROM playerInfos
                        WHERE userId = %s"""
                ,(user_id, )
            )
            money = rows[0][0]
            warlord = rows[0][1]

            # get cards info
            fields = ["id", "protoId", "skill1Id", "skill1Level", "skill1Exp", 
                "skill2Id", "skill2Level", "skill2Exp", "skill3Id", "skill3Level", "skill3Exp"]
            rows = yield util.whdb.runQuery(
                """SELECT {} FROM cardEntities
                        WHERE id IN {} AND ownerId = %s""".format(",".join(fields), str(tuple(cards)))
                ,(user_id, )
            )
            if len(rows) != len(cards):
                raise Exception("error card id")

            # make query result to dict
            master_card = None
            sacrifice_cards = []
            for row in rows:
                card = dict(zip(fields, row))
                if warlord == card["id"]:
                    raise Exception("found warlord")
                if row[0] == cards[0]:
                    master_card = card
                else:
                    sacrifice_cards.append(card)

            if (not master_card) or (not sacrifice_cards):
                raise Exception("error card id")

            # calc add exp
            exp_add = 0
            try:
                for card in sacrifice_cards:
                    exp_add += int(card_tbl.get(card["protoId"], "materialexp"))
            except:
                raise Exception("get add exp error")

            # add exp and calc cost
            skills = [{"id":master_card["skill1Id"], "level":master_card["skill1Level"], "exp":master_card["skill1Exp"]},
                {"id":master_card["skill2Id"], "level":master_card["skill2Level"], "exp":master_card["skill2Exp"]},
                {"id":master_card["skill3Id"], "level":master_card["skill3Level"], "exp":master_card["skill3Exp"]}
            ]
            skillids = card_tbl.gets(master_card["protoId"], "skillid1", "skillid2")
            skillids = [int(skill) for skill in skillids]
            rarities = [int(skill_tbl.get(sid, "rarity")) if sid else 0 for sid in skillids]
            total_cost = 0
            for skill in skills:
                sid = skill["id"]
                level = skill["level"]
                if sid:
                    skill["exp"] += exp_add
                    rarity = int(skill_tbl.get(sid, "rarity"))
                    first_try = True
                    exp_alread_full = False
                    while 1:
                        try:
                            next_exp = skill_level_tbl.get((rarity, level + 1, "exp"))
                            if skill["exp"] < next_exp:
                                break
                            else:
                                level += 1
                        except:
                            skill["exp"] = skill_level_tbl.get((rarity, level, "exp"))
                            if first_try:   # exp full
                                exp_alread_full = True
                            break

                    skill["level"] = level

                    if not exp_full:
                        total_cost += skill_level_tbl.get((rarity, level), "costMoney")

            # check and spend money
            money -= total_cost
            if money < 0:
                raise Exception("not enough money")

            yield util.whdb.runOperation(
                """UPDATE playerInfos SET money=%s
                        WHERE userId=%s"""
                ,(money, user_id)
            )

            # delete absorbed cards
            sacrifice_ids = [str(card["id"]) for card in sacrifice_cards]

            yield util.whdb.runOperation(
                """DELETE FROM cardEntities WHERE id ({}) AND ownerId=%s
                    """.format(",".join(sacrifice_ids))
                ,(user_id, )
            )

            # update card
            yield util.whdb.runOperation(
                """UPDATE cardEntities 
                    SET skill1Level=%s, skill1Exp=%s, 
                        skill2Level=%s, skill2Exp=%s, 
                        skill3Level=%s, skill3Exp=%s
                    WHERE id=%s AND ownerId=%s"""
                ,(  skills[0]["level"], skills[0]["exp"], 
                    skills[1]["level"], skills[1]["exp"], 
                    skills[2]["level"], skills[2]["exp"], 
                    master_card["id"], user_id)
            )

            # reply
            reply = {"error": no_error}
            reply["master"] = master_card
            reply["sacrificers"] = [card["id"] for card in sacrifice_cards]
            reply["money"] = money
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

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
            user_id = session["userid"]

            # param
            try:
                proto = int(self.get_argument("proto"))
                level = int(self.get_argument("level"))
            except:
                send_error(self, err_param)
                return

            # get player's max card number and wagonTemp
            rows = yield util.whdb.runQuery(
                """SELECT maxCardNum, wagonTemp FROM playerInfos
                        WHERE userId=%s"""
                ,(user_id, )
                )
            row = rows[0]
            max_card_num = row[0]
            wagon_temp = Wagon(row[1])

            cards = yield create_cards(user_id, [proto], max_card_num, level)

            # wagon
            for card in cards:
                if not card["inPackage"]:
                    wagon_temp.addCard(card["protoId"], card["id"])

            # real pay and set wagon
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET wagonTemp=%s
                        WHERE userId=%s"""
                ,(json.dumps(wagon_temp.data), user_id)
            )

            # reply
            reply = {"error":no_error}
            reply["card"] = cards[0]
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/card/getpact", GetPact),
    (r"/whapi/card/sell", Sell),
    (r"/whapi/card/evolution", Evolution),
    (r"/whapi/card/sacrifice", Sacrifice),

    (r"/whapi/card/create", Create),
]

# test
# for i in xrange(10000):
#     calc_card_proto_attr(1, 40)
