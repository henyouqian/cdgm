from session import find_session
from error import *
import util
from gamedata import XP_ADD_DURATION

import tornado.web
import adisp

import json
import random
import time

@adisp.async
def async_http_get(url, callback):
    pass
    # get url asynchronously
    # call callback(response) at the end

class Sleep(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            print "xxx"
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            yield async_http_get("xxx")

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/exp/sleep", Sleep),
]
