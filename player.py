from error import *
import util
from gamedata import *
from session import *

import tornado.web
import adisp
import brukva
import simplejson as json
import card
from datetime import datetime, timedelta

class Create(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]
            username = session["username"]

            # param
            try:
                warlord_idx = int(self.get_argument("warlord"))
                if warlord_idx not in xrange(8):
                    raise IndexError("warlord_idx not in [0, 7]")
                warlord_proto_id = WARLORD_ID_BEGIN + warlord_idx
            except:
                send_error(self, err_param)
                return;

            # check exist
            rows = yield util.whdb.runQuery(
                """SELECT 1 FROM playerInfos WHERE userId=%s"""
                ,(userid, )
            )
            if rows:
                send_error(self, "err_player_exist")
                return;

            # add war lord card
            try:
                cards = yield card.create_cards(userid, [warlord_proto_id], INIT_MAX_CARD)
                warlord_card = cards[0]
                warlord_id = warlord_card["id"]
            except:
                send_error(self, "err_create_warlord")
                return

            # init bands
            bands = INIT_BANDS

            for band in bands:
                band["members"][1] = warlord_id

            bands = json.dumps(bands)

            # init items
            items = json.dumps(INIT_ITEMS)

            # wagon
            wagon = json.dumps(INIT_WAGON)

            # create player info
            row_nums = yield util.whdb.runOperation(
                """ INSERT INTO playerInfos
                        (userId, name, warLord, money, inZoneId, lastZoneId, maxCardNum, currentBand, 
                            xp, maxXp, ap, maxAp, bands, items, wagonGeneral, wagonTemp, wagonSocial)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                ,(userid, username, warlord_id, INIT_GOLD, 0, INIT_ZONE_ID, INIT_MAX_CARD, 0
                , INIT_XP, INIT_XP, INIT_AP, INIT_AP, bands, items, wagon, wagon, wagon)
            )

            #reply
            send_ok(self)
        except:
            send_internal_error(self)
        finally:
            self.finish()

class GetInfo(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # query user info
            cols = "userId,name,warlord,money,inZoneId,lastZoneId," \
                    "xp,maxXp,lastXpTime,ap,maxAp,lastApTime,currentBand," \
                    "lastFormation,bands,items,wagonGeneral,wagonTemp,wagonSocial,UTC_TIMESTAMP()"

            sql = "SELECT {} FROM playerInfos WHERE userId=%s".format(cols)
            rows = yield util.whdb.runQuery(
                sql,
                (userid, )
            )
            cols = cols.split(",")
            infos = dict(zip(cols, rows[0]))

            if not rows:
                send_error(self, "err_player_not_exist")
                return;

            curr_time = infos["UTC_TIMESTAMP()"]
            del infos["UTC_TIMESTAMP()"]

            # query cards
            fields_str = """id, protoId, level, exp, inPackage, 
                            skill1Id, skill1Level, skill1Exp, 
                            skill2Id, skill2Level, skill2Exp, 
                            skill3Id, skill3Level, skill3Exp, 
                            hp, atk, def, wis, agi,
                            hpCrystal, atkCrystal, defCrystal, wisCrystal, agiCrystal,
                            hpExtra, atkExtra, defExtra, wisExtra, agiExtra"""
            fields = fields_str.translate(None, "\n ").split(",")
            try:
                rows = yield util.whdb.runQuery(
                    """SELECT {} FROM cardEntities WHERE ownerId=%s""".format(fields_str)
                    ,(userid, )
                )
                cards = [dict(zip(fields, row)) for row in rows]
            except:
                raise Exception("Get cards error. ownerId=%s" % userid)

            # reply
            reply = infos
            reply["error"] = no_error

            #update xp
            xp = infos["xp"]
            max_xp = infos["maxXp"]
            last_xp_time = infos["lastXpTime"]
            if not last_xp_time:
                last_xp_time = datetime(2013, 1, 1)
            dt = curr_time - last_xp_time
            dt = int(dt.total_seconds())
            dxp = dt // XP_ADD_DURATION
            if dxp:
                xp = min(max_xp, xp + dxp)
            if xp == max_xp:
                reply["xpAddRemain"] = 0
            else:
                reply["xpAddRemain"] = dt % XP_ADD_DURATION
            reply["xp"] = xp

            #update ap
            ap = infos["ap"]
            max_ap = infos["maxAp"]
            last_ap_time = infos["lastApTime"]
            if not last_ap_time:
                last_ap_time = datetime(2013, 1, 1)
            dt = curr_time - last_ap_time
            dt = int(dt.total_seconds())
            dap = dt // AP_ADD_DURATION
            if dap:
                ap = min(max_ap, ap + dap)
            if ap == max_ap:
                reply["apAddRemain"] = 0
            else:
                reply["apAddRemain"] = dt % AP_ADD_DURATION
            reply["ap"] = ap

            del reply["lastXpTime"]
            del reply["lastApTime"]
            bands = json.loads(infos["bands"])
            reply["bands"] = [{"index":idx, "formation":band["formation"], "members":band["members"]} for idx, band in enumerate(bands)]
            items = json.loads(infos["items"])
            reply["items"] = [{"id": int(k), "num": v} for k, v in items.iteritems()]
            reply["cards"] = cards
            self.write(json.dumps(reply))
            
        except:
            send_internal_error(self)
        finally:
            self.finish()

# bands=[{"index":0, "formation":23, "members":[34, 643, null, 456, null, 54]}]
class SetBand(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # query player info
            rows = yield util.whdb.runQuery(
                """ SELECT lastFormation, bands, warLord FROM playerInfos
                        WHERE userId=%s"""
                ,(userid, )
            )
            row = rows[0]
            last_formation = row[0]
            db_bands = json.loads(row[1])
            warlord = row[2]

            member_set = set()

            # input
            bands = json.loads(self.request.body)
            for band in bands:
                index = band["index"]
                formation = int(band["formation"])
                members = band["members"]

                # check band index
                if index not in [0, 1, 2]:
                    raise Exception("Band index error:%s" % index)

                # check warlord exist
                if warlord not in members:
                    raise Exception("Warlord must in band:%s" % warlord)

                # check formation
                last_max_num = int(fmt_tbl.get(str(last_formation), "maxNum"))
                max_num = int(fmt_tbl.get(str(formation), "maxNum"))
                if max_num != last_max_num:
                    raise Exception("Invalid formation member number: max_num=%s, last_max_num=%s" % (max_num, last_max_num))
                if formation > last_formation:
                    raise Exception("Formation not available now: formation=%s, last_formation=%s" % (formation, last_formation))

                # check and collect members
                if len(members) != max_num * 2:
                    raise Exception("member_num error")
                mems_not_none = [int(mem) for mem in members if mem or mem==0]
                print members
                ms = set(members)
                ms.discard(None)
                if len(ms) != len(mems_not_none):
                    raise Exception("card entity id repeated")
                member_set |= ms

                db_bands[index] = {"formation":formation, "members":members}

            # check member
            mem_proto_num = len(member_set)
            if mem_proto_num:
                rows = yield util.whdb.runQuery(
                    """ SELECT COUNT(1) FROM cardEntities
                            WHERE ownerId = %s AND id IN ({})""".format(",".join(("%s",)*len(member_set)))
                    ,(userid,) + tuple(member_set)
                )
                count = rows[0][0]

                if count != mem_proto_num:
                    raise Exception("May be one or some cards is not yours")

            # store db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET bands=%s
                        WHERE userid=%s"""
                ,(json.dumps(db_bands), userid)
            )
            
            # reply
            send_ok(self)
            
        except:
            send_internal_error(self)
        finally:
            self.finish()

class UseItem(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            userid = session["userid"]

            # params
            try:
                item_id = self.get_argument("itemid")
            except:
                send_error(self, err_param)
                return;

            # query items info
            conn = yield util.whdb.beginTransaction()
            try:
                rows = yield util.whdb.runQuery(
                    """ SELECT items FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, ), conn
                )
                row = rows[0]
                items = row[0]
                items = json.loads(items)

                # check item count
                item_num = items[item_id]
                if item_num == 0:
                    raise Exception("Not have this item")

                # update item count
                item_num -= 1
                items[item_id] = item_num
                row_nums = yield util.whdb.runOperation(
                    """ UPDATE playerInfos SET items=%s
                            WHERE userId=%s"""
                    ,(json.dumps(items), userid)
                    ,conn
                )
            finally:
                yield util.whdb.commitTransaction(conn)


            # use item(fixme)

            
            
            # reply
            reply = {"error":no_error, "itemId":int(item_id), "itemNum":item_num}
            self.write(json.dumps(reply))
            
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/player/create", Create),
    (r"/whapi/player/getinfo", GetInfo),
    (r"/whapi/player/setband", SetBand),
    (r"/whapi/player/useitem", UseItem),
]

fmt_tbl = util.CsvTbl("data/formations.csv", "id")