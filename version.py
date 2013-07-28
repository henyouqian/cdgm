from error import *
import util

import tornado.web
import adisp

import json


class Version(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        try:
            # reply
            reply = util.new_reply()
            reply["version"] = [0, 6, 3]
            reply["minVersion"] = [0, 6, 3]
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/version", Version),
]
