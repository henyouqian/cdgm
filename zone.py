from error import *
from session import *
import g
import tornado.web
import adisp
import brukva
import simplejson as json
import logging

class Get(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
        
        except:
            send_internal_error(self)
        finally:
            self.finish()


handlers = [
    (r"/whapi/zone/get", Get),
]