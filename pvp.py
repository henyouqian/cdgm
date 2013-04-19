from session import *
from error import *
import g

import tornado.web
import adisp

import simplejson as json
import csv
import random

def make_redis_pvp_list_key(level):
    return "pvpList/lv=" + str(level)

class Request(tornado.web.RequestHandler):
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

            # get player's pvp info
            rows = yield g.whdb.runQuery(
                """SELECT pvpStrength, pvpWinNum FROM playerInfos
                        WHERE userId=%s"""
                ,(user_id, )
                )
            row = rows[0]
            pvp_strength = row[0]
            pvp_win_num = row[1]

            def get_pvp_level(strength):
                return 1

            pvp_level = get_pvp_level(pvp_strength)

            bands = []
            curr_search_lv = pvp_level
            while len(bands) < 3:
                if curr_search_lv == 0:
                    break
                remain = 3 - len(bands)
                key = make_redis_pvp_list_key(curr_search_lv)
                list_len = yield g.redis().llen(key)
                print list_len
                sample_num = min(list_len, remain)
                indices = random.sample(xrange(list_len), sample_num)
                for idx in indices:
                    band = yield g.redis().lindex(key, idx)
                    bands.append(band)

                curr_search_lv -= 1


            # reply
            reply = {"error":no_error}
            reply["bands"] = bands
            
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

class SubmitResult(tornado.web.RequestHandler):
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

            # reply
            reply = {"error":no_error}
              
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/pvp/request", Request),
    (r"/whapi/pvp/submitresult", SubmitResult),
]