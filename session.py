import uuid
import g
import brukva
import adisp
import simplejson as json
import tornado.web

SESSION_TTL = 60*60*24*7

@adisp.async
@adisp.process
def new_session(userid, username, appid, callback):
    uidtokenkey = "{}:usertoken".format(userid)
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
    usertoken = rqHandler.get_cookie("usertoken")
    if not usertoken:
        callback(None)
        return;
    session = yield g.redis().get(usertoken)
    if not session:
        callback(None)
        return
    try:
        session = json.loads(session)
        callback(session)
    except:
        callback(None)