from session import *
from error import *
from gamedata import WAGON_TYPE_TEMP, WAGON_TEMP_DURATION
import util
import card as mdl_card

import tornado.web
import adisp

import json
import datetime

@adisp.async
@adisp.process
def add_cards(wagontype, userid, cards, callback):
    try:
        yield util.whdb.runOperationMany(
            """INSERT INTO wagons
                    (userId, type, count, cardEntity, cardProto) VALUES(%s, %s, %s, %s, %s)
            """
            , tuple(((userid, wagontype, 1, card["id"], card["protoId"]) for card in cards))
        )
        callback(None)
    except Exception as e:
        callback(e)

class Wagon(object):
    """
    [key, itemId, itemNum, time]
    [key, cardEntity, cardProto, time]
    """
    def __init__(self, json_str):
        self.data = json.loads(json_str)

    def addItem(self, item_id, item_num):
        # self.data.append([itemId, itemNum, util.datetime_to_str(util.utc_now())])
        self.data.append(["item:%d,%d"%(item_id, item_num), item_id, item_num, util.datetime_to_str(util.utc_now())])

    def addCard(self, proto_id, card_entityId):
        # self.data.append([-protoId, cardNum, util.datetime_to_str(util.utc_now()), cardEntityId])
        self.data.append(["card:%d"%card_entityId, card_entityId, proto_id, util.datetime_to_str(util.utc_now())])

    @staticmethod
    def transToDict(obj):
        if obj[0].startswith("item"):
            return {"key":obj[0], "itemId":obj[1], "itemNum":obj[2], "time":obj[3]}
        elif obj[0].startswith("card"):
            return {"key":obj[0], "cardEntity":obj[1], "cardProto":obj[2], "time":obj[3]}
        else:
            raise Exception("key error")

    @staticmethod
    def isCard(obj):
        return "cardEntity" in obj


class _List(tornado.web.RequestHandler):
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
                wagon_idxs = list(set([int(s) for s in self.get_argument("wagonidx").split(",")]))
                for idx in wagon_idxs:
                    if idx not in xrange(3):
                        raise Exception("invalid wagon_type")
            except:
                send_error(self, err_param)
                return

            # query wagon data
            field_strs = ["wagonGeneral", "wagonTemp", "wagonSocial"]
            fields = [field_strs[idx] for idx in wagon_idxs]

            rows = yield util.whdb.runQuery(
                """SELECT {} FROM playerInfos
                        WHERE userId=%s""".format(",".join(fields))
                ,(user_id,)
            )

            wagons = rows[0]
            out_wagons = []
            for i, wagon in enumerate(wagons):
                wagon = json.loads(wagon)

                out_wagon = {}
                out_wagon["wagonIdx"] = wagon_idxs[i]
                
                out_items = []

                if wagon_idxs[i] == WAGON_TYPE_TEMP:
                    wagon_expired_removed = []
                    has_expired = False
                    for item_idx, item in enumerate(wagon):
                        out_item = Wagon.transToDict(item)
                        wagon_item_time = util.parse_datetime(out_item["time"])
                        time_delta = datetime.timedelta(seconds=WAGON_TEMP_DURATION)
                        if util.utc_now() > wagon_item_time + time_delta:
                            has_expired = True
                            continue
                        out_items.append(out_item)
                        wagon_expired_removed.append(item)

                    if has_expired:
                        yield util.whdb.runOperation(
                            """UPDATE playerInfos SET wagonTemp=%s
                                    WHERE userId=%s"""
                            ,(json.dumps(wagon_expired_removed), user_id)
                        )
                else:
                    for item_idx, item in enumerate(wagon):
                        out_item = Wagon.transToDict(item)
                        out_items.append(out_item)

                out_wagon["items"] = out_items
                out_wagons.append(out_wagon)

            # reply
            reply = util.new_reply()
            reply["wagons"] = out_wagons
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
                        WHERE userId=%s AND type=%s LIMIT %s,%s""".format(",".join(cols))
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
                key = self.get_argument("key", None)
            except:
                send_error(self, err_param)
                return

            # query
            field_strs = ["wagonGeneral", "wagonTemp", "wagonSocial"]
            rows = yield util.whdb.runQuery(
                """SELECT {}, items, maxCardNum FROM playerInfos
                        WHERE userId=%s""".format(field_strs[wagon_idx])
                ,(user_id,)
            )
            row = rows[0]
            wagon_items = json.loads(row[0])
            items = json.loads(row[1])
            max_card_num = row[2]

            # 
            del_objs = []
            add_items = []
            add_cards = []

            card_accept_remain = None
            find_key = False
            for raw_item in wagon_items:
                wagon_item = Wagon.transToDict(raw_item)
                wagon_item_time = util.parse_datetime(wagon_item["time"])

                # if key specified
                if key:
                    if key != wagon_item["key"]:
                        continue
                    else:
                        find_key = True

                # check expired
                if wagon_idx == WAGON_TYPE_TEMP:
                    time_delta = datetime.timedelta(seconds=WAGON_TEMP_DURATION)
                    if util.utc_now() > wagon_item_time + time_delta:
                        del_objs.append(wagon_item)
                        continue

                # card
                if Wagon.isCard(wagon_item):
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
                        continue
                    else:
                        card_accept_remain -= 1

                    del_objs.append(raw_item)
                    add_cards.append(wagon_item)
                    
                # item
                else:
                    del_objs.append(raw_item)
                    add_items.append(wagon_item)

                if find_key:
                    break

            # del from wagon
            if del_objs:
                wagon_items = [item for item in wagon_items if item not in del_objs]

            # add items
            out_items = []
            if add_items:
                for wagon_item in add_items:
                    wagon_item_id = wagon_item["itemId"]
                    wagon_item_num = wagon_item["itemNum"]
                    if wagon_item_id in items:
                        items[wagon_item_id] += wagon_item_num
                    else:
                        items[wagon_item_id] = wagon_item_num
                    out_items.append({"id": wagon_item_id, "num": wagon_item_num})

            # update player info
            if add_items or del_objs:
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET items=%s, {}=%s
                            WHERE userId=%s""".format(field_strs[wagon_idx])
                    ,(json.dumps(items), json.dumps(wagon_items), user_id)
                )

            # add cards
            out_cards = []
            if add_cards:
                ids = ",".join([str(card["cardEntity"]) for card in add_cards])
                fields = ["id", "protoId", "level", "exp", "inPackage", 
                            "skill1Id", "skill1Level", "skill1Exp", 
                            "skill2Id", "skill2Level", "skill2Exp", 
                            "skill3Id", "skill3Level", "skill3Exp", 
                            "hp", "atk", "def", "wis", "agi",
                            "hpCrystal", "atkCrystal", "defCrystal", "wisCrystal", "agiCrystal",
                            "hpExtra", "atkExtra", "defExtra", "wisExtra", "agiExtra"]

                rows = yield util.whdb.runQuery(
                    """SELECT {} FROM cardEntities 
                            WHERE id IN ({}) AND ownerId=%s AND inPackage=0""".format(",".join(fields), ids)
                    ,(user_id,)
                )
                
                for row in rows:
                    card = dict(zip(fields, row))
                    out_cards.append(card)

                yield util.whdb.runOperation(
                    """UPDATE cardEntities SET inPackage = 1
                            WHERE id IN ({}) AND ownerId=%s""".format(ids)
                    ,(user_id,)
                )

            # reply
            reply = util.new_reply()
            reply["wagonIdx"] = wagon_idx
            reply["keys"] = [obj[0] for obj in del_objs]
            reply["items"] = out_items
            reply["cards"] = out_cards
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
    (r"/whapi/wagon/list", List),
    (r"/whapi/wagon/accept", Accept),
    (r"/whapi/wagon/sellall", SellAll),
]