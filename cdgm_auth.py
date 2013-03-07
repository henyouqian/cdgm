import tornado.web
import adisp
import brukva
import json
import hashlib
from error import *

class Register(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        #parse param
        try:
            username = self.get_argument("username")
            password = self.get_argument("password")
        except:
            send_error(self, err_param)
            return;
        
        #encrypt password
        password = hashlib.sha1(password).digest()

        #write to redis
        rt = yield brukva.c.hsetnx("user_account", username, password)

        #reply
        if rt == 0:
            send_error(self, err_exist)
            return;
        
        self.write('{"error":0}')
        self.finish()

class Login(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        #parse param
        try:
            username = self.get_argument("username")
            password = self.get_argument("password")
        except:
            send_error(self, err_param)
            return
        
        #encrypt password
        password = hashlib.sha1(password).digest()

        #qurey redis
        pw_redis = yield brukva.c.hget("user_account", username)

        if not pw_redis:
            send_error(self, err_not_exist)
            return

        #password match
        if pw_redis != password:
            send_error(self, err_not_match)
            return

        reply = {"error":0}
        self.write(json.dumps(reply))
        self.finish()


handlers = [
    (r"/api/auth/register", Register),
    (r"/api/auth/login", Login),
]