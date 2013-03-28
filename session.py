import uuid
import g
import brukva
import adisp
import simplejson as json
import tornado.web
import config

SESSION_TTL = 60*60*24*7

@adisp.async
@adisp.process
def new_session(userid, username, appid, callback):
    uidtokenkey = "{}/tokenkey".format(userid)
    usertoken = yield g.redis().get(uidtokenkey)
    if usertoken:
        a = yield g.redis().delete(usertoken)

    usertoken = uuid.uuid4().hex
    userinfo = {"userid":userid, "username":username, "appid":appid}  #set userinfo

    rv = yield g.redis().setex(usertoken, SESSION_TTL, json.dumps(userinfo))
    if rv:
        yield g.redis().setex(uidtokenkey, SESSION_TTL, usertoken)
        callback(usertoken)
    else:
        callback(None)

#return {"userid":userid, "appid":appid} or None
@adisp.async
@adisp.process
def find_session(rqHandler, callback):
    def try_auto_auth():
        if config.auto_auth:
            session = {"userid":12, "appid":123}
            callback(session)
            return
        else:
            callback(None)

    usertoken = rqHandler.get_argument("token", None)
    if not usertoken:
        usertoken = rqHandler.get_cookie("token")

    if not usertoken:
        try_auto_auth()
        return;
    session = yield g.redis().get(usertoken)
    if not session:
        try_auto_auth()
        return
    try:
        session = json.loads(session)
        callback(session)
    except:
        try_auto_auth()