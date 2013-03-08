from error import *
import g
from session import *
import config
import tornado.web
import adisp
import brukva
import simplejson as json
import hashlib
import logging
import datetime

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
        password = hashlib.sha1(password).hexdigest()

        #qurey db
        rows = yield g.db.runQuery(
            """SELECT id FROM developer_account 
                    WHERE username=%s AND password=%s"""
            ,(username, password)
        )
        rows = [[2,]]
        if isinstance(rows, Exception):
            logging.error(str(rows))
            send_error(self, err_db)
            return;

        try:
            userid = rows[0][0]
        except:
            send_error(self, err_not_match)
            return

        #session
        usertoken = yield new_session(userid, config.app_id);
        if usertoken == None:
            send_error(self, err_redis)
            return

        reply = {"error":0, "usertoken":usertoken}
        self.write(json.dumps(reply))

        self.set_cookie("usertoken", usertoken, 
                        expires=datetime.datetime.utcnow()+datetime.timedelta(seconds=SESSION_TTL), 
                        path='/api')
        self.finish()


handlers = [
    (r"/api/auth/register", Register),
    (r"/api/auth/login", Login),
]