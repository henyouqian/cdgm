﻿from error import *
import g
from session import *
import config
import tornado.web
import adisp
import brukva
import simplejson as json
import hashlib
import datetime

class Register(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
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
            try:
                row_nums = yield g.authdb.runOperation(
                    "INSERT INTO user_account (username, password) VALUES(%s, %s)"
                    ,(username, password)
                )
            except:
                send_error(self, err_exist)
                return;

            if row_nums != 1:
                send_error(self, err_db)
                return;

            #qurey db
            try:
                rows = yield g.authdb.runQuery(
                    """SELECT id FROM user_account 
                            WHERE username=%s AND password=%s"""
                    ,(username, password)
                )
            except:
                send_error(self, err_db)
                return

            try:
                userid = rows[0][0]
            except:
                send_error(self, err_not_match)
                return

            #login
            usertoken = yield new_session(userid, username, config.app_id);
            if usertoken == None:
                send_error(self, err_redis)
                return

            reply = {"error":no_error, "token":usertoken}
            self.write(json.dumps(reply))
            self.set_cookie("token", usertoken, 
                            expires=datetime.datetime.utcnow()+datetime.timedelta(seconds=SESSION_TTL), 
                            path='/') #fixme expires and path
            
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Login(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
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
            try:
                rows = yield g.authdb.runQuery(
                    """SELECT id FROM user_account 
                            WHERE username=%s AND password=%s"""
                    ,(username, password)
                )
            except:
                send_error(self, err_db)
                return

            try:
                userid = rows[0][0]
            except:
                send_error(self, err_not_match)
                return

            #session
            usertoken = yield new_session(userid, username, config.app_id);
            if usertoken == None:
                send_error(self, err_redis)
                return

            # check player exist
            player_exist = False
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT 1 FROM playerInfos WHERE userId=%s"""
                    ,(userid, )
                )
                try:
                    player_exist = bool(rows[0][0])
                except:
                    pass
            except:
                send_error(self, err_db)
                return;

            # reply
            reply = {"error":no_error, "token":usertoken, "playerExist":player_exist}
            self.write(json.dumps(reply))

            self.set_cookie("token", usertoken, 
                            expires=datetime.datetime.utcnow()+datetime.timedelta(seconds=SESSION_TTL), 
                            path='/') #fixme expires and path
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Test1(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        send_error(self, err_param)
        self.finish()

class Test2(tornado.web.RequestHandler):
    def get(self):
        send_error(self, err_param)


handlers = [
    (r"/authapi/register", Register),
    (r"/authapi/login", Login),
    (r"/authapi/test1", Test1),
    (r"/authapi/test2", Test2),
]