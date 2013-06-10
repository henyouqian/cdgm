from session import find_session
from error import *
import util
from card import card_tbl, create_cards, calc_card_proto_attr, warlord_level_tbl, card_level_tbl, is_war_lord, skill_level_tbl, skill_tbl
from zone import zone_tbl
from player import fmt_tbl

import tornado.web
import adisp
import json

class CheckAccount(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            session = yield find_session(self)
            if not session or session["username"] != "admin":
                send_error(self, "err_auth")
                return

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

class GetPlayerInfo(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            session = yield find_session(self)
            if not session or session["username"] != "admin":
                send_error(self, "err_auth")
                return

            # param
            username = self.get_argument("userName")

            # get userid
            rows = yield util.authdb.runQuery(
                """SELECT id FROM user_account 
                        WHERE username=%s"""
                ,(username,)
            )
            if not rows:
                raise Exception("player not exist")

            userid = rows[0][0]

            # get player info
            cols = ["userId","name","money","lastZoneId",
                    "xp","maxXp","ap","maxAp","maxCardNum","maxTradeNum",
                    "lastFormation","items"]

            rows = yield util.whdb.runQuery(
                "SELECT {} FROM playerInfos WHERE userId=%s".format(",".join(cols)),
                (userid, )
            )
            playerInfo = dict(zip(cols, rows[0]))
            playerInfo["items"] = json.loads(playerInfo["items"])

            # get cards
            cols = ["id", "protoId", "level"]
            rows = yield util.whdb.runQuery(
                """SELECT {} FROM cardEntities WHERE ownerId=%s""".format(",".join(cols))
                ,(userid, )
            )
            cards = [dict(zip(cols, row)) for row in rows]
            for card in cards:
                proto = card["protoId"]
                card["name"], card["rarity"], card["evolution"] = card_tbl.gets(proto, "name", "rarity", "evolution")

            # reply
            reply = util.new_reply()
            reply["playerInfo"] = playerInfo
            reply["cards"] = cards
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetItemNum(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            itemid = int(self.get_argument("itemId"))
            itemnum = int(self.get_argument("itemNum"))

            # get item
            rows = yield util.whdb.runQuery(
                "SELECT items FROM playerInfos WHERE userId=%s",
                (userid, )
            )
            items = json.loads(rows[0][0])

            # set item
            oldnum = items.get(str(itemid), 0)
            items[str(itemid)] = itemnum
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET items=%s
                        WHERE userId=%s"""
                ,(json.dumps(items), userid)
            )

            # reply
            reply = util.new_reply()
            reply["items"] = items
            reply["change"] = {"id": itemid, "from": oldnum, "to": itemnum}
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetLastZoneId(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            last_zoneid = int(self.get_argument("lastZoneId"))
            try:
                zoneid = zone_tbl.get(last_zoneid, "id")
            except:
                raise Exception("invalid zoneid")

            # update db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET lastZoneId=%s
                        WHERE userId=%s"""
                ,(last_zoneid, userid)
            )

            # reply
            reply = util.new_reply()
            reply["lastZoneId"] = last_zoneid
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetMaxCardNum(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            max_card_num = int(self.get_argument("maxCardNum"))
            max_card_num = max(0, min(100, max_card_num))

            # update db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET maxCardNum=%s
                        WHERE userId=%s"""
                ,(max_card_num, userid)
            )

            # reply
            reply = util.new_reply()
            reply["maxCardNum"] = max_card_num
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetMaxTradeNum(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            max_trade_num = int(self.get_argument("maxTradeNum"))
            max_trade_num = max(0, min(10, max_trade_num))

            # update db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET maxTradeNum=%s
                        WHERE userId=%s"""
                ,(max_trade_num, userid)
            )

            # reply
            reply = util.new_reply()
            reply["maxTradeNum"] = max_trade_num
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetLastFormation(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            last_formation = int(self.get_argument("lastFormation"))
            try:
                formation_id = fmt_tbl.get(last_formation, "id")
            except:
                raise Exception("invalid formation id")

            # update db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET lastFormation=%s
                        WHERE userId=%s"""
                ,(last_formation, userid)
            )

            # reply
            reply = util.new_reply()
            reply["lastFormation"] = last_formation
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetMoney(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            money = int(self.get_argument("money"))
            money = max(0, min(10000000, money))

            # update db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET money=%s
                        WHERE userId=%s"""
                ,(money, userid)
            )

            # reply
            reply = util.new_reply()
            reply["money"] = money
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetAp(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            ap = self.get_argument("ap", None)
            maxap = self.get_argument("maxAp", None)
            if ap:
                ap = int(ap)
            if maxap:
                maxap = int(maxap)
            
            if ap == None and maxap == None:
                raise Exception("need param ap or mapAp")

            # query db
            rows = yield util.whdb.runQuery(
                "SELECT ap, maxAp FROM playerInfos WHERE userId=%s",
                (userid, )
            )
            _ap, _maxAp = rows[0]

            if ap == None:
                ap = _ap
            if maxap == None:
                maxap = _maxAp

            ap = min(ap, maxap)

            yield util.whdb.runOperation(
                """UPDATE playerInfos SET ap=%s, maxAp=%s
                    WHERE userId=%s"""
                ,(ap, maxap, userid)
            )

            # reply
            reply = util.new_reply()
            reply["ap"] = ap
            reply["maxAp"] = maxap
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetXp(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            xp = self.get_argument("xp", None)
            maxxp = self.get_argument("maxXp", None)
            if xp:
                xp = int(xp)
            if maxxp:
                maxxp = int(maxxp)
            
            if xp == None and maxxp == None:
                raise Exception("need param xp or maxXp")

            # query db
            rows = yield util.whdb.runQuery(
                "SELECT xp, maxXp FROM playerInfos WHERE userId=%s",
                (userid, )
            )
            _xp, _maxXp = rows[0]

            if xp == None:
                xp = _xp
            if maxxp == None:
                maxxp = _maxXp

            xp = min(xp, maxxp)

            yield util.whdb.runOperation(
                """UPDATE playerInfos SET xp=%s, maxXp=%s
                    WHERE userId=%s"""
                ,(xp, maxxp, userid)
            )

            # reply
            reply = util.new_reply()
            reply["xp"] = xp
            reply["maxXp"] = maxxp
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class AddCard(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            protoid = int(self.get_argument("protoId"))
            level = int(self.get_argument("level"))

            # get max card number
            rows = yield util.whdb.runQuery(
                """SELECT maxCardNum FROM playerInfos
                    WHERE userid=%s"""
                ,(userid,)
            )
            max_card_num = rows[0][0]

            # update db
            proto_ids = [protoid]
            cards = yield create_cards(userid, proto_ids, max_card_num, level)
            card = cards[0]
            card["name"], card["rarity"], card["evolution"] = card_tbl.gets(protoid, "name", "rarity", "evolution")

            # reply
            reply = util.new_reply()
            reply["card"] = card
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

class SetCardLevel(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            cardid = int(self.get_argument("cardId"))
            level = int(self.get_argument("level"))

            # get proto
            rows = yield util.whdb.runQuery(
                """SELECT protoId FROM cardEntities
                    WHERE id=%s"""
                ,(cardid,)
            )
            try:
                protoid = rows[0][0]
            except:
                raise Exception("card id is invalid")

            try:
                hp, atk, _def, wis, agi = calc_card_proto_attr(protoid, level)
                lvtbl = warlord_level_tbl if is_war_lord(protoid) else card_level_tbl
                exp = lvtbl.get(level, "exp")
            except:
                raise Exception("level is invalid")

            # update db
            yield util.whdb.runOperation(
                """UPDATE cardEntities SET level=%s, hp=%s, atk=%s, def=%s, wis=%s, agi=%s, exp=%s
                        WHERE id=%s"""
                ,(level, hp, atk, _def, wis, agi, exp, cardid)
            )

            # reply
            reply = util.new_reply()
            reply["cardId"] = cardid
            reply["level"] = level
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetCardSkillLevel(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # param
            userid = int(self.get_argument("userId"))
            cardid = int(self.get_argument("cardId"))
            index = int(self.get_argument("index"))
            level = int(self.get_argument("level"))

            if index not in (1, 2, 3):
                raise Exception("index not in (1, 2, 3)")

            # get proto
            rows = yield util.whdb.runQuery(
                """SELECT protoId, skill1Id, skill2Id, skill3Id FROM cardEntities
                    WHERE id=%s"""
                ,(cardid,)
            )
            try:
                protoid, skill1id, skill2id, skill3id = rows[0]
                skillids = [skill1id, skill2id, skill3id]
                skillid = skillids[index-1]
            except:
                raise Exception("invalid card id")

            try:
                rarity = skill_tbl.get(skillid, "rarity")
            except:
                raise Exception("invalid index")

            try:
                exp = skill_level_tbl.get((rarity, level), "exp")
            except:
                raise Exception("invalid level")

            # update db
            yield util.whdb.runOperation(
                """UPDATE cardEntities SET skill{0}Level=%s, skill{0}Exp=%s
                        WHERE id=%s""".format(index)
                ,(level, exp, cardid)
            )

            # reply
            reply = util.new_reply()
            reply["cardId"] = cardid
            reply["level"] = level
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/admin/checkAccount", CheckAccount),
    (r"/whapi/admin/setItemNum", SetItemNum),
    (r"/whapi/admin/getPlayerInfo", GetPlayerInfo),
    (r"/whapi/admin/setLastZoneId", SetLastZoneId),
    (r"/whapi/admin/setMaxCardNum", SetMaxCardNum),
    (r"/whapi/admin/setMaxTradeNum", SetMaxTradeNum),
    (r"/whapi/admin/setLastFormation", SetLastFormation),
    (r"/whapi/admin/setMoney", SetMoney),
    (r"/whapi/admin/setAp", SetAp),
    (r"/whapi/admin/setXp", SetXp),
    (r"/whapi/admin/addCard", AddCard),
    (r"/whapi/admin/setCardLevel", SetCardLevel),
    (r"/whapi/admin/setCardSkillLevel", SetCardSkillLevel),

]
