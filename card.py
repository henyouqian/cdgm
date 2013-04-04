from session import *
from error import *
import g
from util import CsvTbl, CsvTblMulKey

import tornado.web
import adisp

import simplejson as json
from itertools import repeat, imap
from random import randint


card_tbl = CsvTbl("data/cards.csv", "ID")
grow_tbl = CsvTblMulKey("data/cardGrowthMappings.csv", "type", "level")
evo_tbl = CsvTblMulKey("data/cardEvolutions.csv", "masterCardId", "evolverCardId")
evo_cost_tbl = CsvTblMulKey("data/cardEvolutionCosts.csv", "masterCardRarity", "evolverCardRarity")

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

def is_war_lord(entity_id):
    return entity_id >= 119 and entity_id <= 226


@adisp.async
@adisp.process
def create(owner_id, proto_id, level, callback):
    try:
        hp, atk, _def, wis, agi = calc_card_proto_attr(proto_id, level)
        conn = yield g.whdb.beginTransaction()
        try:
            row_nums = yield g.whdb.runOperation(
                """ INSERT INTO cardEntities
                        (hp, atk, def, wis, agi, protoId, ownerId)
                        VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                ,(hp, atk, _def, wis, agi, proto_id, owner_id), conn
            )
            rows = yield g.whdb.runQuery("SELECT LAST_INSERT_ID()", None, conn)
        finally:
            yield g.whdb.commitTransaction(conn)

        if row_nums != 1:
            raise Exception("db insert error")
        entity_id = rows[0][0]
        card = {"id":entity_id, "protoId":proto_id, "level":level, "exp":0, "hp":hp, "atk":atk, "def":_def, "wis":wis, "agi":agi}
        card.update({"hpCrystal":0, "atkCrystal":0, "defCrystal":0, "wisCrystal":0, "agiCrystal":0})
        card.update({"hpExtra":0, "atkExtra":0, "defExtra":0, "wisExtra":0, "agiExtra":0})
        card.update({})
        callback(card)
    except Exception as e:
        callback(e)

# ====================================================
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

            try:
                card = yield create(user_id, proto, level)
            except:
                send_error(self, "err_card_type_or_level")
                return

            # reply
            reply = {"error":no_error}
            reply["card"] = card
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

class Random(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return

            proto = randint(0, 63)

            entity_id = yield create(session["userid"], proto, 1)
            self.write('{"error"="%s", "protoId"=%s, "entityId"=%s}' % (no_error, proto, entity_id))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Sell(tornado.web.RequestHandler):
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
                entity_id = int(self.get_argument("id"))
            except:
                send_error(self, err_param)
                return

            # query card info and check owner
            rows = yield g.whdb.runQuery(
                """SELECT protoId FROM cardEntities
                        WHERE id = %s and ownerId = %s"""
                ,(entity_id, user_id)
            )

            try:
                proto_id = rows[0][0]
            except:
                send_error(self, err_not_exist)
                return

            if not proto_id or is_war_lord(proto_id):
                send_error(self, err_permission)
                return

            # query player info
            rows = yield g.whdb.runQuery(
                        """SELECT gold, bands, isInZone FROM playerInfos
                                WHERE userId=%s"""
                        ,(user_id, )
                    )
            row = rows[0]
            gold = row[0]
            bands = json.loads(row[1])
            isInZone = row[2]
            if isInZone:
                send_error(self, "err_in_zone")
                return

            # add gold
            price = int(card_tbl.get(proto_id, "price"))
            gold += price

            # delete if in band
            inband = False
            for band in bands:
                for idx, member in enumerate(band["members"]):
                    if member == entity_id:
                        band[idx] = None
                        inband = True
                        break

            # update playerInfo
            if inband:
                yield g.whdb.runOperation(
                        """UPDATE playerInfos SET gold=%s, bands=%s
                                WHERE userId=%s"""
                        ,(gold, json.dumps(bands), user_id)
                    )
            else:
                yield g.whdb.runOperation(
                        """UPDATE playerInfos SET gold=%s
                                WHERE userId=%s"""
                        ,(gold, user_id)
                    )

            # delete card
            yield g.whdb.runOperation(
                "DELETE FROM cardEntities WHERE id = %s",
                entity_id
            )

            # reply
            reply = {"error":no_error}
            reply["id"] = entity_id
            reply["gold"] = gold
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

            fields_str = """id, protoId, level, exp, skillLevel, skillExp, addSkill1, addSkill2,
                            hp, atk, def, wis, agi,
                            hpCrystal, atkCrystal, defCrystal, wisCrystal, agiCrystal,
                            hpExtra, atkExtra, defExtra, wisExtra, agiExtra"""
            fields = fields_str.translate(None, "\n ").split(",")

            # query card info from db and check owner
            rows = yield g.whdb.runQuery(
                """SELECT {}
                        FROM cardEntities
                        WHERE (id=%s OR id=%s) AND ownerId = %s""".format(fields_str)
                ,(card_id1, card_id2, user_id)
            )
            if len(rows) != 2:
                send_error(self, "err_card_id")
                return
            
            cards = [dict(zip(fields, row)) for row in rows]
            # make cards[0] primary
            if cards[0]["id"] == card_id2:
                cards[0], cards[1] = cards[1], cards[0]

            card1, card2 = cards
            
            # spend gold
            rarity1 = card_tbl.get(card1["protoId"], "rarity")
            rarity2 = card_tbl.get(card2["protoId"], "rarity")
            cost = int(evo_cost_tbl.get((rarity1, rarity2), "cost"))
            rows = yield g.whdb.runQuery(
                        """SELECT gold, bands, isInZone FROM playerInfos
                                WHERE userId=%s"""
                        ,(user_id, )
                    )
            row = rows[0]
            gold = row[0]
            bands = json.loads(row[1])
            isInZone = row[2]
            if isInZone:
                send_error(self, "err_in_zone")
                return

            if gold < cost:
                send_error(self, "err_gold_not_enough")
                return
            gold -= cost

            # look up evolution table
            try:
                proto_id = int(evo_tbl.get((str(card1["protoId"]), str(card2["protoId"])), "afterCardId"))
            except:
                send_error(self, "err_card_type")
                return

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


            yield g.whdb.runOperation(
                    """UPDATE cardEntities SET protoId=%s, hp=%s, atk=%s, def=%s, wis=%s, agi=%s, 
                            hpExtra=%s, atkExtra=%s, defExtra=%s, wisExtra=%s, agiExtra=%s
                            WHERE id=%s"""
                    ,(proto_id, hp, atk, _def, wis, agi, hp_ex, atk_ex, def_ex, wis_ex, agi_ex, card1["id"])
                )

            yield g.whdb.runOperation(
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
                yield g.whdb.runOperation(
                        """UPDATE playerInfos SET gold=%s, bands=%s
                                WHERE userId=%s"""
                        ,(gold, json.dumps(bands), user_id)
                    )
            else:
                yield g.whdb.runOperation(
                        """UPDATE playerInfos SET gold=%s
                                WHERE userId=%s"""
                        ,(gold, user_id)
                    )

            # reply
            reply = {"error":no_error}
            reply["gold"] = gold
            reply["delCardId"] = card2["id"]
            reply["evoCard"] = card1

            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Absorb(tornado.web.RequestHandler):
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
            try:
                print self.request.body, "xxxxxxx"
                cards = json.loads(self.request.body)
                card_num = len(cards)
                if card_num < 2 or card_num > 9:
                    raise Exception("card_num < 2 or card_num > 9")
                for card in cards:
                    if type(card) != int:
                        raise Exception("id must be int")
            except:
                send_error(self, err_post)
                return

            master_card = cards[0]
            absorb_cards = cards[1:]

            rows = yield g.whdb.runQuery(
                """SELECT id, protoId FROM cardEntities
                        WHERE id IN {} AND ownerId = %s""".format(str(tuple(cards)))
                ,(user_id, )
            )
            print rows

            send_ok(self)
        except:
            send_internal_error(self)
        finally:
            self.finish()
            

handlers = [
    (r"/whapi/card/create", Create),
    (r"/whapi/card/random", Random),
    (r"/whapi/card/sell", Sell),
    (r"/whapi/card/evolution", Evolution),
    (r"/whapi/card/absorb", Absorb),
]

# test
# for i in xrange(10000):
#     calc_card_proto_attr(1, 40)
