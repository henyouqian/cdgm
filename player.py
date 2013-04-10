from error import *
import g
from gamedata import *
from session import *
from util import CsvTbl

import tornado.web
import adisp
import brukva
import simplejson as json
import card

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
                warlord_proto_id = 117 + warlord_idx
            except:
                send_error(self, err_param)
                return;

            # check exist
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT 1 FROM playerInfos WHERE userId=%s"""
                    ,(userid, )
                )
            except:
                send_error(self, err_db)
                return;
            if rows:
                send_error(self, err_exist)
                return;

            # add war lord card
            try:
                warlord_card = yield card.create(userid, warlord_proto_id, 1)
                print warlord_card
                warlord_id = warlord_card["id"]
            except:
                send_error(self, "err_create_card")
                return

            # init bands
            bands = INIT_BANDS

            for band in bands:
                band["members"][1] = warlord_id

            bands = json.dumps(bands)


            # init items
            items = INIT_ITEMS
            items = json.dumps(items)


            # create player info
            try:
                row_nums = yield g.whdb.runOperation(
                    """ INSERT INTO playerInfos
                            (userId, name, warLord, money, isInZone, lastZoneId,
                                xp, maxXp, ap, maxAp, bands, items)
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    ,(userid, username, warlord_id, INIT_GOLD, 0, INIT_ZONE_ID
                    , INIT_XP, INIT_XP, INIT_AP, INIT_AP, bands, items)
                )
            except:
                send_error(self, err_db)
                return;

            if row_nums != 1:
                send_error(self, err_db)
                return;

            # response
            # resp = {"error":no_error, "id":userid}
            # resp["name"] = username
            # resp["isInZone"] = False
            # resp["lastZoneId"] = 0
            # resp["ap"] = INIT_AP
            # resp["maxAp"] = INIT_AP
            # self.write(json.dumps(resp))
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
            try:
                cols = "userId,name,warlord,money,isInZone,lastZoneId," \
                        "xp,maxXp,lastXpTime,ap,maxAp,lastApTime," \
                        "lastFormation,bands,items"

                sql = "SELECT {} FROM playerInfos WHERE userId=%s".format(cols)
                rows = yield g.whdb.runQuery(
                    sql,
                    (userid, )
                )
                cols = cols.split(",")
                infos = dict(zip(cols, rows[0]))
            except:
                send_error(self, err_db)
                return;
            if not rows:
                send_error(self, err_not_exist)
                return;

            # query cards
            fields_str = """id, protoId, level, exp, 
                            skill1Id, skill1Level, skill1Exp, 
                            skill2Id, skill2Level, skill2Exp, 
                            skill3Id, skill3Level, skill3Exp, 
                            hp, atk, def, wis, agi,
                            hpCrystal, atkCrystal, defCrystal, wisCrystal, agiCrystal,
                            hpExtra, atkExtra, defExtra, wisExtra, agiExtra"""
            fields = fields_str.translate(None, "\n ").split(",")
            try:
                rows = yield g.whdb.runQuery(
                    """SELECT {} FROM cardEntities WHERE ownerId=%s""".format(fields_str)
                    ,(userid, )
                )
                cards = [dict(zip(fields, row)) for row in rows]
            except:
                send_error(self, err_db)
                return;

            # reply
            reply = infos
            reply["error"] = no_error
            reply["lastXpTime"] = str(infos["lastXpTime"]) if infos["lastXpTime"] else None
            reply["lastApTime"] = str(infos["lastApTime"]) if infos["lastApTime"] else None
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
            try:
                rows = yield g.whdb.runQuery(
                    """ SELECT lastFormation, bands, warLord FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, )
                )
                row = rows[0]
                last_formation = row[0]
                db_bands = row[1]
                warlord = row[2]
            except:
                send_error(self, err_db)
                return

            db_bands = json.loads(db_bands)

            member_set = set()
            # input
            try:
                bands = json.loads(self.request.body)
                for band in bands:
                    index = band["index"]
                    formation = int(band["formation"])
                    members = band["members"]

                    # check band index
                    if index not in [0, 1, 2]:
                        send_error(self, err_index)
                        return

                    # check warlord exist
                    if warlord not in members:
                        send_error(self, "err_warlord")
                        return

                    # check formation
                    try:
                        max_num = int(fmt_tbl.get(str(formation), "maxNum"))
                        if max_num != last_max_num:
                            raise Exception("Invalid formation member number")
                        if formation > last_formation:
                            raise Exception("Formation not available now")
                    except:
                        send_error(self, "err_formation")
                        return

                    # check and collect members
                    try:
                        if len(members) != max_num * 2:
                            raise Exception("member_num error")
                        mems_not_none = [int(mem) for mem in members if mem]
                        ms = set(members)
                        ms.discard(None)
                        if len(ms) != len(mems_not_none):
                            raise Exception("card entity id repeated")
                        member_set |= ms

                    except:
                        send_error(self, "err_members")
                        return

                    db_bands[index] = {"formation":formation, "members":members}

            except:
                send_error(self, err_post)
                return

            # check member
            mem_proto_num = len(member_set)
            if mem_proto_num:
                try:
                    rows = yield g.whdb.runQuery(
                        """ SELECT COUNT(1) FROM cardEntities
                                WHERE ownerId = %s AND id in %s"""
                        ,(userid, tuple(member_set))
                    )
                    count = rows[0][0]
                except:
                    send_error(self, err_db)
                    return

                if count != mem_proto_num:
                    send_error(self, "err_members", "Not your card")
                    return

            # store db
            try:
                yield g.whdb.runOperation(
                    """UPDATE playerInfos SET bands=%s
                            WHERE userid=%s"""
                    ,(json.dumps(db_bands), userid)
                )
            except:
                send_error(self, err_db)
                return
            
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
            conn = yield g.whdb.beginTransaction()
            try:
                rows = yield g.whdb.runQuery(
                    """ SELECT items FROM playerInfos
                            WHERE userId=%s"""
                    ,(userid, )
                    , conn
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
                try:
                    row_nums = yield g.whdb.runOperation(
                        """ UPDATE playerInfos SET items=%s
                                WHERE userId=%s"""
                        ,(json.dumps(items), userid)
                        ,conn
                    )
                except:
                    send_error(self, err_db)
                    return;
            except:
                send_error(self, err_not_exist)
                return
            finally:
                yield g.whdb.commitTransaction(conn)


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

fmt_tbl = CsvTbl("data/formations.csv", "id")