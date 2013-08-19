from error import *
import util
from session import *
import config
from tornado import web, httpclient, escape
import adisp
import brukva
import json
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
                callback = self.get_argument("callback", None)

                if len(username)==0 or len(password)==0:
                    raise Exception("username or password too short")
            except:
                send_error(self, err_param)
                return;
            
            #encrypt password
            password = hashlib.sha1(password).hexdigest()

            #insert to db
            try:
                row_nums = yield util.authdb.runOperation(
                    "INSERT INTO user_account (username, password) VALUES(%s, %s)"
                    ,(username, password)
                )
            except:
                send_error(self, "err_account_exist")
                return;

            #qurey db
            rows = yield util.authdb.runQuery(
                """SELECT id FROM user_account 
                        WHERE username=%s"""
                ,(username,)
            )

            userid = rows[0][0]

            #new session
            usertoken = yield new_session(userid, username, config.app_id);
            if usertoken == None:
                raise Exception("error new_session")

            self.set_cookie("token", usertoken, 
                            expires=datetime.datetime.utcnow()+datetime.timedelta(seconds=SESSION_TTL), 
                            path='/') #fixme expires and path

            reply = util.new_reply()
            reply["token"] = usertoken
            
            if callback:
                self.write("%s(%s)" % (callback, json.dumps(reply)))
            else:
                self.write(json.dumps(reply))
            
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
                callback = self.get_argument("callback", None)
            except:
                send_error(self, err_param)
                return
            
            #encrypt password
            password = hashlib.sha1(password).hexdigest()

            #qurey db
            rows = yield util.authdb.runQuery(
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
            tutorial_step = 0
            rows = yield util.whdb.runQuery(
                """SELECT 1, tutorialStep FROM playerInfos WHERE userId=%s"""
                ,(userid, )
            )
            try:
                player_exist = bool(rows[0][0])
                tutorial_step = rows[0][1]
            except:
                player_exist = False


            # reply
            self.set_cookie("token", usertoken, 
                            expires=datetime.datetime.utcnow()+datetime.timedelta(seconds=SESSION_TTL), 
                            path='/') #fixme expires and path

            reply = util.new_reply()
            reply["token"] = usertoken
            reply["playerExist"] = player_exist
            reply["tutorialStepIndex"] = tutorial_step

            if callback:
                self.write("%s(%s)" % (callback, json.dumps(reply)))
            else:
                self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class Login91(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            #parse param
            try:
                name = self.get_argument("name")
                uin = self.get_argument("uin")
                session = self.get_argument("session")
                callback = self.get_argument("callback", None)
            except:
                send_error(self, err_param)
                return
            
            # auth with 91 server
            http_client = tornado.httpclient.AsyncHTTPClient()
            sourceStr = "{}{}{}{}{}".format(config.app_id_91, 4, uin, session, config.app_secret_91)
            signStr = hashlib.md5()
            signStr.update(sourceStr.encode('utf-8'))
            sign = signStr.hexdigest()

            url = "http://service.sj.91.com/usercenter/AP.aspx?Appid={}&Act=4&Uin={}&SessionId={}&Sign={}".format(
                config.app_id_91, escape.url_escape(uin), escape.url_escape(session), sign)
            response = yield adisp.async(http_client.fetch)(url, request_timeout=5)

            if response.error:
                raise Exception("fetch from 91 server error")

            try:
                body = json.loads(response.body)
                if body["ErrorCode"] != 1:
                    raise Exception
            except:
                raise Exception("91 server auth failed")

            # if account not exists, create new. else login
            rows = yield util.authdb.runQuery(
                """SELECT id FROM user_account 
                        WHERE uin91=%s"""
                ,(uin, )
            )
            try:
                userid = rows[0][0]
            except:
                yield util.whdb.runOperation(
                    "INSERT INTO user_account (uid91) VALUES(%s)"
                    ,(uin,)
                )
                rows = yield util.authdb.runQuery(
                    """SELECT id FROM user_account 
                            WHERE uin91=%s"""
                    ,(uin,)
                )
                userid = rows[0][0]

            #session
            usertoken = yield new_session(userid, name, config.app_id);
            if usertoken == None:
                raise Exception("error new_session")

            # check player exist
            player_exist = False
            rows = yield util.whdb.runQuery(
                """SELECT 1 FROM playerInfos WHERE userId=%s"""
                ,(userid, )
            )
            try:
                player_exist = bool(rows[0][0])
            except:
                player_exist = False

            # reply
            self.set_cookie("token", usertoken, 
                            expires=datetime.datetime.utcnow()+datetime.timedelta(seconds=SESSION_TTL), 
                            path='/') #fixme expires and path

            reply = util.new_reply()
            reply["token"] = usertoken
            reply["playerExist"] = player_exist

            if callback:
                self.write("%s(%s)" % (callback, json.dumps(reply)))
            else:
                self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


handlers = [
    (r"/authapi/register", Register),
    (r"/authapi/login", Login),
    (r"/authapi/login91", Login91),
]

