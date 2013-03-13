from error import *
import g
from session import *
import tornado.web
import adisp
import brukva
import simplejson as json
import logging

class Addcard(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        # session
        session = yield find_session(self)
        if not session:
            send_error(self, err_auth)
            return
        
        self.finish()


handlers = [
    (r"/whapi/cheat/addcard", Addcard),
]