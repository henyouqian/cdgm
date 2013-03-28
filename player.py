from error import *
import g
from gamedata import *
from session import *
import tornado.web
import adisp
import brukva
import simplejson as json
import logging
import card

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
            userid = session["userid"]
            username = session["username"]

            # param
            try:
                warlord_idx = int(self.get_argument("warlord"))
                if warlord_idx not in xrange(8):
                    raise IndexError("warlord_idx not in [0, 7]")
                warlord_proto_id = 117 + warlord_idx
            except:
                send_error(self, err_param)
                return;

            # check exist
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT 1 FROM playerInfos WHERE userId=%s"""
                    ,(userid, )
                )
            except Exception as e:
                logging.error(e)
                send_error(self, err_db)
                return;
            if rows:
                send_error(self, err_exist)
                return;

            # add war lord card
            entity_id = yield card.create(warlord_proto_id, userid)

            # create player info
            try:
                row = (userid, username, entity_id, 0, 0, INIT_XP, INIT_XP, INIT_AP, INIT_AP
                    , INIT_SILVER_COIN, INIT_BRONZE_COIN)
                row_nums = yield g.whdb.runOperation(
                    """ INSERT INTO playerInfos
                            (userId, name, warLord, isInZone, lastZoneId,
                                xp, maxXp, ap, maxAp, silverCoin, bronzeCoin)
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    ,row
                )
            except Exception as e:
                logging.debug(e)
                send_error(self, err_db)
                return;

            if row_nums != 1:
                send_error(self, err_db)
                return;

            # response
            # resp = {"error":no_error, "id":userid}
            # resp["name"] = username
            # resp["isInZone"] = False
            # resp["lastZoneId"] = 0
            # resp["ap"] = INIT_AP
            # resp["maxAp"] = INIT_AP
            # self.write(json.dumps(resp))
            send_ok(self)
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Getinfo(tornado.web.RequestHandler):
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

            # query user info
            try:
                rows = yield g.whdb.runQuery(
                    """ SELECT name, isInZone, lastZoneId, 
                            ap, maxAp, silverCoin, bronzeCoin
                            FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, )
                )
            except Exception as e:
                logging.error(e)
                send_error(self, err_db)
                return;
            if not rows:
                send_error(self, err_not_exist)
                return;

            # response
            resp = {"error":no_error, "id":userid}
            try:
                row = rows[0]
                resp["name"] = row[0]
                resp["isInZone"] = bool(row[1])
                resp["lastZoneId"] = row[2]
                resp["ap"] = row[3]
                resp["maxAp"] = row[4]
                self.write(json.dumps(resp))
            except:
                send_error(self, err_db)
                return;
            
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/player/create", Create),
    (r"/whapi/player/getinfo", Getinfo),
]