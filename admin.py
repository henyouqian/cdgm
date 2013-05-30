from session import find_session
from error import *
import util
from card import card_tbl
from zone import zone_tbl
from player import fmt_tbl

import tornado.web
import adisp
import json

class GetPlayerInfo(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
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
            cols = "userId,name,money,lastZoneId," \
                    "xp,maxXp,ap,maxAp,maxCardNum,maxTradeNum," \
                    "lastFormation,items"

            rows = yield util.whdb.runQuery(
                "SELECT {} FROM playerInfos WHERE userId=%s".format(cols),
                (userid, )
            )

            cols = cols.split(",")
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


class setItemNum(tornado.web.RequestHandler):
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


handlers = [
    (r"/whapi/admin/setItemNum", setItemNum),
    (r"/whapi/admin/getPlayerInfo", GetPlayerInfo),
    (r"/whapi/admin/setLastZoneId", SetLastZoneId),
    (r"/whapi/admin/setMaxCardNum", SetMaxCardNum),
    (r"/whapi/admin/setMaxTradeNum", SetMaxTradeNum),
    (r"/whapi/admin/setLastFormation", SetLastFormation),
    (r"/whapi/admin/setMoney", SetMoney),
]
