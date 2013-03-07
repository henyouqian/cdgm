from error import *
import g
import tornado.web
import adisp
import brukva
import json
import hashlib
import logging

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
        password = hashlib.sha1(password).hexdigest()

        #insert to db
        rv = yield g.db.runOperation(
            "INSERT INTO developer_account (username, password) VALUES(%s, %s)"
            ,(username, password)
        )

        if isinstance(rv, Exception):
            logging.error(str(rv))
            send_error(self, err_exist)
            return;

        if rv == 0:
            logging.error(str(rv))
            send_error(self, err_db)
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
        pw_redis = yield g.redis.hget("user_account", username)

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