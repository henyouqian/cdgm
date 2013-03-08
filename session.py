import uuid
import g
import brukva
import adisp
import simplejson as json

SESSION_TTL = 60*60

@adisp.async
@adisp.process
def new_session(userid, appid, callback):
    uidtokenkey = "{}:usertoken".format(userid)
    usertoken = yield g.redis.get(uidtokenkey)
    if usertoken:
        a = yield g.redis.delete(usertoken)

    usertoken = uuid.uuid4().hex
    userinfo = [userid, appid]  #set userinfo

    rv = yield g.redis.setex(usertoken, SESSION_TTL, json.dumps(userinfo))
    if rv:
        yield g.redis.setex(uidtokenkey, SESSION_TTL, usertoken)
        callback(usertoken)
    else:
        callback(None)

#return userinfo:[userid, appid] or None
@adisp.async
@adisp.process
def find_session(usertoken, callback):
    userinfo = yield g.redis.get(usertoken)
    if not userinfo:
        callback(None)
        return
    try:
        userinfo = json.loads(userinfo)
        callback(userinfo)
    except:
        callback(None)