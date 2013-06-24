from session import find_session
from error import *
import util

import tornado.web
import adisp

import json
import random
import datetime

PVP_ID_SERIAL = "PVP_ID_SERIAL"
PVP_Z_KEY = "PVP_Z_KEY"

class AddTestRecord(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            n = 1
            curr_id = yield util.redis().incrby(PVP_ID_SERIAL, n)
            records = []
            pipe = util.redis_pipe()
            for d in xrange(n):
                curr_id += 1
                score = random.random()*10000
                pipe.zadd(PVP_Z_KEY, score, curr_id)
            yield util.redis_pipe_execute(pipe)

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/pvp/addtestrecord", AddTestRecord),
]
