from session import *
from error import *
import g
from gamedata import WAGON_TYPE_TEMP, WAGON_TEMP_DURATION
import util

import tornado.web
import adisp

import simplejson as json
import datetime

class Wagon(object):
    """
    [type, num, time]
        if type > 0: It is item, type is item's id
        if type < 0: It is card, value is card proto id
        num is the number of items or cards
        time is when put into the wagon, the type is string of datetime
    """
    def __init__(self, json_str):
        self.data = json.loads(json_str)

    def addItem(self, itemId, itemNum):
        self.data.append([itemId, itemNum, util.datetime_to_str(util.utc_now())])

    def addCard(self, cardId, cardNum, cardEntityId):
        self.data.append([-cardId, cardNum, util.datetime_to_str(util.utc_now()), cardEntityId])

    def getItem(self, obj):
        return {"id":obj[0], "num":obj[1], "time":util.parse_datetime(obj[2])}

    def getCard(self, obj):
        return {"id":obj[1], "num":obj[1], "time":util.parse_datetime(obj[2]), "cardEntityId":obj[3]}


class List(tornado.web.RequestHandler):
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

            rows = yield g.whdb.runQuery(
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
                for item_idx, item in enumerate(wagon):
                    out_item = {}
                    out_item["id"] = item[0]
                    out_item["num"] = item[1]
                    out_item["time"] = item[2]
                    if len(item) == 4:
                        out_item["cardEntityId"] = item[3]
                    out_items.append(out_item)

                out_wagon["items"] = out_items
                out_wagons.append(out_wagon)

            # reply
            reply = {"error":no_error}
            reply["wagons"] = out_wagons
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
                item_idx = int(self.get_argument("itemidx"))
            except:
                send_error(self, err_param)
                return

            # query
            field_strs = ["wagonGeneral", "wagonTemp", "wagonSocial"]
            rows = yield g.whdb.runQuery(
                """SELECT {}, items, maxCardNum FROM playerInfos
                        WHERE userId=%s""".format(field_strs[wagon_idx])
                ,(user_id,)
            )

            wagon_items = json.loads(rows[0][0])
            items = json.loads(rows[0][1])
            items = {(k,v) for k, v in items.iteritems()}
            max_card_num = rows[0][2]

            # accept
            wagon_item = wagon_items[item_idx]
            wagon_item_id = wagon_item[0]
            wagon_item_num = wagon_item[1]
            wagon_item_time = util.parse_datetime(wagon_item[2])

            # check expired
            if wagon_idx == WAGON_TYPE_TEMP:
                time_delta = datetime.timedelta(seconds=WAGON_TEMP_DURATION)

                if util.utc_now() > wagon_item_time + time_delta:
                    # del from playerInfo's wagon
                    del wagon_items[item_idx]
                    yield g.whdb.runOperation(
                        """UPDATE playerInfos SET {}=%s
                                WHERE userId=%s""".format(field_strs[wagon_idx])
                        ,(json.dumps(wagon_items), user_id)
                    )
                    if wagon_item_id < 0:
                        # del from cardEntities
                        yield g.whdb.runOperation(
                            """DELETE FROM cardEntities
                                    WHERE id=%s AND ownerId=%s"""
                            ,(wagon_item[3], user_id)
                        )

                    reply = {"error":"err_expired"}
                    reply["index"] = item_idx
                    self.write(json.dumps(reply))
                    return

            # add item
            out_item = None
            out_card = None

            # add card
            if wagon_item_id < 0:
                card_proto_id = -wagon_item_id
                card_entity_id = wagon_item[3]

                # check whether card is full
                rows = yield g.whdb.runQuery(
                    """SELECT COUNT(1) FROM cardEntities
                            WHERE ownerId=%s AND inPackage=1"""
                    ,(user_id,)
                )
                card_num = rows[0][0]
                if card_num >= max_card_num:
                    send_error(self, "err_card_full")
                    return

                del wagon_items[item_idx]
                yield g.whdb.runOperation(
                    """UPDATE playerInfos SET {}=%s
                            WHERE userId=%s""".format(field_strs[wagon_idx])
                    ,(json.dumps(wagon_items), user_id)
                )
                # update card info
                cols = """id, protoId, level, exp, inPackage, 
                            skill1Id, skill1Level, skill1Exp, 
                            skill2Id, skill2Level, skill2Exp, 
                            skill3Id, skill3Level, skill3Exp, 
                            hp, atk, def, wis, agi,
                            hpCrystal, atkCrystal, defCrystal, wisCrystal, agiCrystal,
                            hpExtra, atkExtra, defExtra, wisExtra, agiExtra"""
                rows = yield g.whdb.runQuery(
                    """SELECT {} FROM cardEntities 
                            WHERE id=%s AND ownerId=%s AND inPackage=0""".format(cols)
                    ,(card_entity_id, user_id)
                )
                out_card = rows[0][0]

                yield g.whdb.runOperation(
                    """UPDATE cardEntities SET inPackage = 1
                            WHERE id=%s AND ownerId=%s"""
                    ,(card_entity_id, user_id)
                )
                
            # add item
            else:
                if wagon_item_id in items:
                    items[wagon_item_id] += wagon_item_num
                else:
                    items[wagon_item_id] = wagon_item_num

                del wagon_items[item_idx]
                yield g.whdb.runOperation(
                    """UPDATE playerInfos SET items=%s, {}=%s
                            WHERE userId=%s""".format(field_strs[wagon_idx])
                    ,(json.dumps(items), json.dumps(wagon_items), user_id)
                )
                out_item = {"id":wagon_item_id, "num":wagon_item_num}

            # reply
            reply = {"error":no_error}
            reply["wagonIdx"] = wagon_idx
            reply["itemIdx"] = item_idx
            reply["item"] = out_item
            reply["card"] = out_card
            self.write(json.dumps(reply))

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/wagon/list", List),
    (r"/whapi/wagon/accept", Accept),
]