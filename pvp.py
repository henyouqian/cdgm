from session import find_session
from error import *
import util
from gamedata import AP_ADD_DURATION

import tornado.web
import adisp

import simplejson as json
import random
import datetime

def make_redis_pvp_list_key(level):
    return "pvpList/lv=" + str(level)

def calc_pvp_level(strength):
    return strength / 10

class Request(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # get player's pvp info
            rows = yield util.whdb.runQuery(
                """SELECT pvpStrength, pvpWinStreak FROM playerInfos
                        WHERE userId=%s""",
                (user_id, )
            )
            row = rows[0]
            pvp_strength = row[0]
            pvp_win_streak = row[1]

            pvp_level = calc_pvp_level(pvp_strength)

            bands = []
            curr_search_lv = pvp_level
            while len(bands) < 3:
                if curr_search_lv == 0:
                    break
                remain = 3 - len(bands)
                key = make_redis_pvp_list_key(curr_search_lv)
                list_len = yield util.redis().llen(key)
                print list_len
                sample_num = min(list_len, remain)
                indices = random.sample(xrange(list_len), sample_num)
                for idx in indices:
                    band = yield util.redis().lindex(key, idx)
                    bands.append(band)

                curr_search_lv -= 1

            # reply
            reply = {"error": no_error}
            reply["bands"] = bands

            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class StartBattle(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # parse post data
            indata = json.loads(self.request.body)
            foe_grp_idx = indata["foeGroupIdx"]
            band = indata["band"]
            formation = band["formation"]
            members = band["members"]
            allout = indata["allout"]
            use_item = indata["useItem"]
            if use_item not in (0, 1, 2):
                raise Exception("invalid useItem")

            # get player info for later use
            rows = yield util.whdb.runQuery(
                """SELECT ap, maxAp, lastApTime, items FROM playerInfos
                        WHERE userId=%s"""
                ,(user_id, )
            )
            row = rows[0]
            ap = row[0]
            max_ap = row[1]
            last_ap_time = row[2]
            if not last_ap_time:
                last_ap_time = util.utc_now()
            items = json.loads(row[3])
            items = {int(k):v for k, v in items.iteritems()}

            # update AP from last time
            curr_time = util.utc_now()
            dt = curr_time - last_ap_time
            dt = int(dt.total_seconds())
            dap = dt // AP_ADD_DURATION
            if dap:
                ap = min(max_ap, ap + dap)
            if ap == max_ap:
                last_ap_time = curr_time
            else:
                last_ap_time = curr_time - datetime.timedelta(seconds = dt % AP_ADD_DURATION)

            # consume AP
            update_items = False
            need_ap = 3 if allout else 1
            if need_ap > ap:
                dap = need_ap - ap
                if use_item == 0:
                    raise Exception("not enough ap, need useItem")
                elif use_item == 1:
                    item_num = items.get(10, 0)
                    if item_num < dap:
                        raise Exception("not enough small item")
                    items[10] -= dap
                    update_items = True
                elif use_item == 2:
                    item_num = items.get(11, 0)
                    if item_num < dap:
                        raise Exception("not enough big item")
                    items[11] -= dap
                    update_items = True

            if not update_items:
                ap -= need_ap

            yield util.whdb.runOperation(
                """UPDATE playerInfos SET ap=%s, lastApTime=%s, items=%s 
                        WHERE userId=%s"""
                ,(ap, last_ap_time, json.dumps(items), user_id)
            )

            # update user pvp band info
            ## get card entity attr
            fields = ["id", "protoId", "level", "skill1Id", "skill2Id", "skill3Id", 
                "hp", "atk", "def", "wis", "agi", 
                "hpCrystal", "atkCrystal", "defCrystal", "wisCrystal", "agiCrystal",
                "hpExtra", "atkExtra", "defExtra", "wisExtra", "agiExtra"]
            members_no_null = [m for m in members if m]
            member_num = len(members_no_null)
            rows = yield util.whdb.runQuery(
                """SELECT {} FROM cardEntities
                        WHERE ownerId=%s AND id IN ({}) AND inPackage=1
                """.format(",".join(fields), ",".join((str(m) for m in members if m)))
                ,(user_id)
            )
            if len(rows) != member_num:
                raise Exception("include invalid member")

            members_data = []
            for row in rows:
                member_data = dict(zip(fields, row))
                member_data["hp"] += member_data["hpCrystal"] + member_data["hpExtra"]
                member_data["atk"] += member_data["atkCrystal"] + member_data["atkExtra"]
                member_data["def"] += member_data["defCrystal"] + member_data["defExtra"]
                member_data["wis"] += member_data["wisCrystal"] + member_data["wisExtra"]
                member_data["agi"] += member_data["agiCrystal"] + member_data["agiExtra"]
                del member_data["hpCrystal"]
                del member_data["atkCrystal"]
                del member_data["defCrystal"]
                del member_data["wisCrystal"]
                del member_data["agiCrystal"]
                del member_data["hpExtra"]
                del member_data["atkExtra"]
                del member_data["defExtra"]
                del member_data["wisExtra"]
                del member_data["agiExtra"]
                members_data.append(member_data)

            ## calc pvp strength
            def calcPvpStrength(members):
                # fixme
                return 1000

            pvp_strength = calcPvpStrength(members)
            pvp_level = calc_pvp_level(pvp_strength)

            ## add to redis
            key = make_redis_pvp_list_key(pvp_level)
            pvp_data = {"formation":formation, "strength":pvp_strength, "members":members_data}

            pipe = util.redis_pipe()
            pipe.sadd("tset", "t")
            pipe.scard("tset")
            # res = pipe.execute()
            res = yield util.redis_pipe_execute(pipe)
            # res = yield adisp.async(pipe.execute, cbname='callbacks')()

            # reply
            reply = util.new_reply()
            reply["res"] = res
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

class SubmitResult(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # reply
            reply = util.new_reply()
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/pvp/request", Request),
    (r"/whapi/pvp/startbattle", StartBattle),
    (r"/whapi/pvp/submitresult", SubmitResult),
]
