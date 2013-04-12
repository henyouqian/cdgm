from error import *
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
                send_error(self, "err_account_exist")
                return;

            #qurey db
            rows = yield g.authdb.runQuery(
                """SELECT id FROM user_account 
                        WHERE username=%s"""
                ,(username,)
            )

            userid = rows[0][0]

            #new session
            usertoken = yield new_session(userid, username, config.app_id);
            if usertoken == None:
                raise Exception("error new_session")

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
            rows = yield g.authdb.runQuery(
                """SELECT id FROM user_account 
                        WHERE username=%s AND password=%s"""
                ,(username, password)
            )

            try:
                userid = rows[0][0]
            except:
                send_error(self, err_not_match)
                return

            #session
            usertoken = yield new_session(userid, username, config.app_id);
            if usertoken == None:
                raise Exception("error new_session")

            # check player exist
            player_exist = False
            rows = yield g.whdb.runQuery(
                """SELECT 1 FROM playerInfos WHERE userId=%s"""
                ,(userid, )
            )
            try:
                player_exist = bool(rows[0][0])
            except:
                player_exist = false

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


handlers = [
    (r"/authapi/register", Register),
    (r"/authapi/login", Login),
]