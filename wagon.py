from session import *
from error import *
from gamedata import WAGON_TEMP_DURATION, WAGON_INDEX_TEMP
import util
import card as mdl_card

import tornado.web
import adisp

import json
import datetime

@adisp.async
@adisp.process
def add_cards(wagonidx, userid, cards, desc, callback):
    try:
        if not cards:
            raise Exception("empty cards")

        yield util.whdb.runOperationMany(
            """INSERT INTO wagons
                    (userId, wagonIdx, count, cardEntity, cardProto, descText) VALUES(%s, %s, %s, %s, %s, %s)
            """
            , tuple(((userid, wagonidx, 1, card["id"], card["protoId"], desc) for card in cards))
        )
        cols = ["wagonGeneral", "wagonTemp", "wagonSocial"]
        yield util.whdb.runOperation(
            """UPDATE playerInfos SET {0}={0}+%s
                    WHERE userId=%s""".format(cols[wagonidx])
            ,(len(cards), userid)
        )
        callback(None)
    except Exception as e:
        callback(e)


@adisp.async
@adisp.process
def add_items(wagonidx, userid, items, desc, callback):
    try:
        if not items:
            raise Exception("empty items")

        yield util.whdb.runOperationMany(
            """INSERT INTO wagons
                    (userId, wagonIdx, count, itemId, descText) VALUES(%s, %s, %s, %s, %s)
            """
            , tuple(((userid, wagonidx, item["num"], item["id"], desc) for item in items))
        )
        cols = ["wagonGeneral", "wagonTemp", "wagonSocial"]
        yield util.whdb.runOperation(
            """UPDATE playerInfos SET {0}={0}+%s
                    WHERE userId=%s""".format(cols[wagonidx])
            ,(len(items), userid)
        )
        callback(None)
    except Exception as e:
        callback(e)


class GetCount(tornado.web.RequestHandler):
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

            rows = yield util.whdb.runQuery(
                """SELECT wagonGeneral, wagonTemp, wagonSocial FROM playerInfos
                        WHERE userId=%s"""
                ,(user_id,)
            )
            row = rows[0]

            # reply
            reply = util.new_reply()
            reply["general"] = row[0]
            reply["temp"] = row[1]
            reply["social"] = row[2]
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class List(tornado.web.RequestHandler):
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

            # post input
            post_input = json.loads(self.request.body)
            wagon_idx = post_input["wagonIdx"]
            start_idx = post_input["startIdx"]
            count = post_input["count"]

            if wagon_idx not in (0, 1, 2):
                raise Exception("wrong wagonIdx: %s" % wagon_idx)
            if start_idx < 0:
                raise Exception("wrong startIdx: %s" % start_idx)
            if count <= 0 or count > 20:
                raise Exception("wrong count: %s" % start_idx)

            # query wagon data
            cols = ["id", "count", "cardEntity", "cardProto", "itemId", "descText", "time"]
            rows = yield util.whdb.runQuery(
                """SELECT {} FROM wagons
                        WHERE userId=%s AND wagonIdx=%s LIMIT %s,%s""".format(",".join(cols))
                ,(user_id, wagon_idx, start_idx, count)
            )

            wagon_entries = [dict(zip(cols, row)) for row in rows]
            items = []
            cards = []
            for entry in wagon_entries:
                d = {"key":entry["id"], "desc":entry["descText"], "time":util.datetime_to_str(entry["time"])}
                if entry["itemId"]:
                    d["itemId"] = entry["itemId"]
                    d["itemNum"] = entry["count"]
                    items.append(d)
                else:
                    d["cardEntity"] = entry["cardEntity"]
                    d["cardProto"] = entry["cardProto"]
                    cards.append(d)

            # reply
            reply = util.new_reply()
            reply["waginIdx"] = wagon_idx
            reply["totalCount"] = 0
            reply["items"] = items
            reply["cards"] = cards
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class Accept(tornado.web.RequestHandler):
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

            # post input
            post_input = json.loads(self.request.body)
            keys = post_input["keys"]
            keys = map(int, keys)

            # query
            cols = ["id", "wagonIdx", "count", "cardEntity", "cardProto", "itemId", "descText", "time"]
            rows = yield util.whdb.runQuery(
                """SELECT {} FROM wagons
                        WHERE userId=%s AND id in ({})""".format(",".join(cols), ",".join(map(str, keys)))
                ,(user_id,)
            )
            wagon_objs = [dict(zip(cols, row)) for row in rows]

            rows = yield util.whdb.runQuery(
                """SELECT items, maxCardNum, wagonGeneral, wagonTemp, wagonSocial FROM playerInfos
                        WHERE userId=%s"""
                ,(user_id,)
            )
            row = rows[0]
            items = json.loads(row[0])
            max_card_num = row[1]
            wagon_obj_num = [row[2], row[3], row[4]]

            # 
            del_objs = []
            accepted_items = []
            accepted_cards = []
            expired_cards = []
            card_accept_remain = None
            info = ""
            del_nums = [0, 0, 0]

            for obj in wagon_objs:
                # check if expired
                if obj["wagonIdx"] == WAGON_INDEX_TEMP:
                    time_delta = datetime.timedelta(seconds=WAGON_TEMP_DURATION)
                    if util.utc_now() > obj["time"] + time_delta:
                        del_objs.append(obj)
                        info = "expired"
                        del_nums[obj["wagonIdx"]] += 1
                        expired_cards.append(obj)
                        continue
                # item
                if obj["itemId"]:
                    accepted_items.append(obj)
                    del_objs.append(obj)
                    del_nums[obj["wagonIdx"]] += 1
                # card
                else:
                    if card_accept_remain == None:
                        rows = yield util.whdb.runQuery(
                            """SELECT COUNT(1) FROM cardEntities
                                    WHERE ownerId=%s AND inPackage=1"""
                            ,(user_id,)
                        )
                        card_num = rows[0][0]
                        card_accept_remain = max_card_num - card_num

                    # check if full
                    if card_accept_remain <= 0:
                        info = "card_full"
                        continue
                    else:
                        card_accept_remain -= 1
                        accepted_cards.append(obj)
                        del_objs.append(obj)
                        del_nums[obj["wagonIdx"]] += 1
                    
            # add items
            out_items = []
            for item in accepted_items:
                itemId = item["itemId"]
                itemNum = item["count"]
                strItemId = str(itemId)
                if strItemId in items:
                    items[strItemId] += itemNum
                else:
                    items[strItemId] = itemNum
                out_items.append({"id":itemId, "num":itemNum})

            if accepted_items:
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET items=%s
                            WHERE userId=%s"""
                    ,(json.dumps(items), user_id)
                )

            # add cards
            out_cards = []
            if accepted_cards:
                ids = ",".join([str(card["cardEntity"]) for card in accepted_cards])
                cols = ["id", "protoId", "level", "exp", "inPackage", 
                            "skill1Id", "skill1Level", "skill1Exp", 
                            "skill2Id", "skill2Level", "skill2Exp", 
                            "skill3Id", "skill3Level", "skill3Exp", 
                            "hp", "atk", "def", "wis", "agi",
                            "hpCrystal", "atkCrystal", "defCrystal", "wisCrystal", "agiCrystal",
                            "hpExtra", "atkExtra", "defExtra", "wisExtra", "agiExtra"]

                rows = yield util.whdb.runQuery(
                    """SELECT {} FROM cardEntities 
                            WHERE id IN ({}) AND ownerId=%s AND inPackage=0""".format(",".join(cols), ids)
                    ,(user_id,)
                )
                
                for row in rows:
                    card = dict(zip(cols, row))
                    out_cards.append(card)

                yield util.whdb.runOperation(
                    """UPDATE cardEntities SET inPackage = 1
                            WHERE id IN ({}) AND ownerId=%s""".format(ids)
                    ,(user_id,)
                )

            # del from wagon
            if del_objs:
                ids = ",".join([str(obj["id"]) for obj in del_objs]) 
                yield util.whdb.runOperation(
                    """DELETE FROM wagons
                            WHERE id IN ({}) AND userId=%s""".format(ids)
                    ,(user_id,)
                )

            # del expired cards
            if expired_cards:
                ids = ",".join([str(obj["cardEntity"]) for obj in del_objs])
                yield util.whdb.runOperation(
                    """DELETE FROM cardEntities
                            WHERE id IN ({}) AND userId=%s""".format(ids)
                    ,(user_id,)
                )

            # wagon obj count
            for i in xrange(3):
                wagon_obj_num[i] -= del_nums[i]

            cols = ["wagonGeneral", "wagonTemp", "wagonSocial"]
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET wagonGeneral=%s, wagonTemp=%s, wagonSocial=%s
                        WHERE userId=%s"""
                ,(wagon_obj_num[0], wagon_obj_num[1], wagon_obj_num[2], user_id)
            )

            # reply
            reply = util.new_reply()
            reply["acceptedKeys"] = [obj["id"] for obj in del_objs]
            reply["items"] = out_items
            reply["cards"] = out_cards
            reply["info"] = info
            reply["generalCount"] = wagon_obj_num[0]
            reply["tempCount"] = wagon_obj_num[1]
            reply["socialCount"] = wagon_obj_num[2]
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()


class SellAll(tornado.web.RequestHandler):
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

            # params
            try:
                wagon_idx = int(self.get_argument("wagonidx"))
            except:
                send_error(self, err_param)
                return

            # query
            field_strs = ["wagonGeneral", "wagonTemp", "wagonSocial"]
            rows = yield util.whdb.runQuery(
                """SELECT {} FROM playerInfos
                        WHERE userId=%s""".format(field_strs[wagon_idx])
                ,(user_id,)
            )
            row = rows[0]
            wagon_items = json.loads(row[0])

            # 
            cards = []
            items = []
            money_add = 0
            for raw_item in wagon_items:
                wagon_item = Wagon.transToDict(raw_item)
                if Wagon.isCard(wagon_item):
                    cards.append(wagon_item)
                    cardProto = wagon_item["cardProto"]
                    money_add += int(mdl_card.card_tbl.get(cardProto, "price"))
                else:
                    items.append(raw_item)

            if cards:
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET {}=%s, money=money+%s
                            WHERE userId=%s""".format(field_strs[wagon_idx])
                    ,(json.dumps(items), money_add, user_id)
                )
                yield util.whdb.runOperation(
                    """DELETE FROM cardEntities
                            WHERE id IN ({}) AND ownerId=%s""".format(",".join([str(card["cardEntity"]) for card in cards]))
                    ,(user_id,)
                )



            # reply
            reply = util.new_reply()
            reply["wagonIdx"] = wagon_idx
            reply["moneyAdd"] = money_add
            reply["delKeys"] = [card["key"] for card in cards]
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/wagon/getcount", GetCount),
    (r"/whapi/wagon/list", List),
    (r"/whapi/wagon/accept", Accept),
    (r"/whapi/wagon/sellall", SellAll),
]