from error import *
import util
from session import *
import tornado.web
import adisp
import brukva
import json
import logging

class Teleport(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # param
            try:
                x = int(self.get_argument("x"))
                y = int(self.get_argument("y"))
            except:
                send_error(self, err_param)
                return

            # select form db
            rows = yield util.whdb.runQuery(
                """ SELECT zoneCache FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            try:
                cache = json.loads(row[0])
            except:
                raise Exception("not in zone")

            cache["currPos"] = [x, y]

            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s WHERE userid=%s"""
                ,(json.dumps(cache), userid)
            )

            # reply
            reply = util.new_reply()
            reply["x"] = x
            reply["y"] = y
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()


class RedGold(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # param
            try:
                red = int(self.get_argument("red"))
                gold = int(self.get_argument("gold"))
            except:
                send_error(self, err_param)
                return

            # select form db
            rows = yield util.whdb.runQuery(
                """ SELECT zoneCache FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            try:
                cache = json.loads(row[0])
            except:
                raise Exception("not in zone")

            cache["redCase"] = red
            cache["goldCase"] = gold

            yield util.whdb.runOperation(
                """UPDATE playerInfos SET zoneCache=%s WHERE userid=%s"""
                ,(json.dumps(cache), userid)
            )

            # reply
            reply = util.new_reply()
            reply["red"] = red
            reply["gold"] = gold
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/cheat/teleport", Teleport),
    (r"/whapi/cheat/redGold", RedGold),
]