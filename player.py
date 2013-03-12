from error import *
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
        # session
        session = yield find_session(self)
        if not session:
            send_error(self, err_auth)
            return
        userid = session["userid"]
        username = session["username"]

        # query user info
        e, rows = yield g.whdb.runQuery(
            """ SELECT name, currentBandId, isInMap, lastMapId, 
                    ap, maxAp
                    FROM playerInfos
                    WHERE userId=%s"""
            ,(userid, )
        )
        if e:
            logging.error(e)
            send_error(self, err_db)
            return;

        # insert user info
        if not rows:
            row = (userid, username, 0, 0, 0, INITIAL_AP, INITIAL_AP)
            e, row_nums = yield g.whdb.runOperation(
                """ INSERT INTO playerInfos
                        (userId, name, currentBandId, isInMap, lastMapId,
                            ap, maxAp)
                        VALUES(%s, %s, %s, %s, %s, %s, %s)"""
                ,row
            )
            if e or row_nums != 1:
                logging.error(e)
                send_error(self, err_db)
                return;
            rows = (row[1:],)

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
        
        self.finish()

handlers = [
    (r"/whapi/player/getinfo", Getinfo),
]