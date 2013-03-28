from session import *
from error import *
import g
from util import CsvTbl, CsvTblMulKey

import tornado.web
import adisp

import simplejson as json
from itertools import repeat, imap
import logging
from random import randint


card_tbl = CsvTbl("data/cards.csv", "ID")
grow_tbl = CsvTblMulKey("data/cardGrowthMappings.csv", "type", "level")

# # test
# row = grow_tbl.get_row("1", "11")
# print row
# print grow_tbl.get_value(row, "curve")
# print grow_tbl.get(("1", "3"),"curve")

# row = card_tbl.get_row("1")
# print tuple(card_tbl.get_values(row, "name", "cardtype"))

# for __ in xrange(10000):
#   grow_tbl.get(("1", "11"),"curve")

# calc for hp, atk, def, wis, agi
def calc_card_proto_attr(proto_id, level):
    proto = card_tbl.get_row(str(proto_id))
    min_attrs = card_tbl.get_values(proto, 
        "basehp", "baseatk", "basedef", "basewis", "baseagi")
    max_attrs = card_tbl.get_values(proto, 
        "maxhp", "maxatk", "maxdef", "maxwis", "maxagi")
    maxlevel, growtype = card_tbl.get_values(proto, "maxlevel", "growtype")
    if level > int(maxlevel):
        raise ValueError("card proto: level > maxlevel. proto_id=%s"%proto_id)

    growmin = float(grow_tbl.get((growtype, "1"), "curve"))
    growmax = float(grow_tbl.get((growtype, maxlevel), "curve"))
    growcurr = float(grow_tbl.get((growtype, str(level)), "curve"))

    def lerp(min, max, f):
        min = float(min)
        max = float(max)
        return min + (max - min)*f

    f = (growcurr - growmin) / (growmax - growmin)
    return tuple(imap(lerp, min_attrs, max_attrs, repeat(f)))

def is_war_lord(entity_id):
    return entity_id >= 119 and entity_id <= 226


@adisp.async
@adisp.process
def create(proto_id, owner_id, callback):
    hp, atk, _def, wis, agi = calc_card_proto_attr(proto_id, 1)
    try:
        conn = yield g.whdb.beginTransaction()
        row_nums = yield g.whdb.runOperation(
            """ INSERT INTO cardEntitys
                    (hp, atk, def, wis, agi, cardId, ownerId)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)"""
            ,(hp, atk, _def, wis, agi, proto_id, owner_id)
            ,conn
        )
        rows = yield g.whdb.runQuery("SELECT LAST_INSERT_ID()", None, conn)
        yield g.whdb.commitTransaction(conn)
        if row_nums != 1:
            raise Exception("db insert error")
        entity_id = rows[0][0]
        callback(entity_id)
    except Exception as e:
        logging.debug(e)
        raise;

# ====================================================
class Create(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            yield create(2, 12)

            # response
            send_ok(self)

        except:
            send_internal_error(self)
        finally:
            self.finish()

class Random(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return

            proto = randint(0, 63)

            entity_id = yield create(proto, session["userid"])
            self.write('{"error"="%s", "cardId"=%s, "entityId"=%s}' % (no_error, proto, entity_id))
        except:
            send_internal_error(self)
        finally:
            self.finish()

class Sell(tornado.web.RequestHandler):
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

            # param
            try:
                entity_id = self.get_argument("entityid")
            except:
                send_error(self, err_param)
                return

            # db
            rows = yield g.whdb.runQuery(
                """SELECT cardId FROM cardEntitys
                        WHERE id = %s and ownerId = %s"""
                ,(entity_id, user_id)
            )

            try:
                print rows, entity_id, user_id
                proto_id = rows[0][0]
            except:
                send_error(self, err_not_exist)
                return

            if not proto_id or is_war_lord(proto_id):
                send_error(self, err_permission)
                return

            #fixme: add gold
            yield g.whdb.runOperation(
                "DELETE FROM cardEntitys WHERE id = %s",
                entity_id
            )

            self.write('{"error"="%s", "cardId"=%s, "entityId"=%s}' % (no_error, proto_id, entity_id))
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/card/create", Create),
    (r"/whapi/card/random", Random),
    (r"/whapi/card/sell", Sell),
]

# test
# for i in xrange(10000):
#     calc_card_proto_attr(1, 40)
