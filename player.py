﻿from error import *
import g
from gamedata import *
from session import *
import tornado.web
import adisp
import brukva
import simplejson as json
import logging

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
            e, rows = yield g.whdb.runQuery(
                """ SELECT name, currentBandId, isInMap, lastMapId, 
                        ap, maxAp, silverCoin, bronzeCoin
                        FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            if e:
                logging.error(e)
                send_error(self, err_db)
                return;
            if not rows:
                send_error(self, err_not_exist)
                return;

            # response
            resp = {"error":0, "id":userid}
            try:
                row = rows[0]
                resp["name"] = row[0]
                resp["currentBandId"] = row[1]
                resp["isInMap"] = row[2]
                resp["lastMapId"] = row[3]
                resp["ap"] = row[4]
                resp["maxAp"] = row[5]
                self.write(json.dumps(resp))
            except:
                send_error(self, err_db)
                return;
            
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
            userid = session["userid"]
            username = session["username"]

            # param
            try:
                warlord_idx = int(self.get_argument("warlord"))
            except:
                send_error(self, err_param)
                return;

            # check exist
            e, rows = yield g.whdb.runQuery(
                """SELECT 1 FROM playerInfos WHERE userId=%s"""
                ,(userid, )
            )

            if e:
                logging.error(e)
                send_error(self, err_db)
                return;
            if rows:
                send_error(self, err_exist)
                return;

            # create player info
            row = (userid, username, 0, 0, 0, INIT_AP, INIT_AP
                , INIT_SILVER_COIN, INIT_BRONZE_COIN)
            e, row_nums = yield g.whdb.runOperation(
                """ INSERT INTO playerInfos
                        (userId, name, currentBandId, isInMap, lastMapId,
                            ap, maxAp, silverCoin, bronzeCoin)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                ,row
            )
            if e or row_nums != 1:
                if e: logging.error(e)
                send_error(self, err_db)
                return;

            # response
            resp = {"error":0, "id":userid}
            resp["name"] = row[1]
            resp["currentBandId"] = row[2]
            resp["isInMap"] = row[3]
            resp["lastMapId"] = row[4]
            resp["ap"] = row[5]
            resp["maxAp"] = row[6]
            resp["silverCoin"] = row[7]
            resp["bronzeCoin"] = row[8]
            self.write(json.dumps(resp))
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/player/getinfo", Getinfo),
    (r"/whapi/player/create", Create)
]