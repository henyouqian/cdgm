from error import *
import util
from gamedata import *
from session import *
from csvtable import *

import tornado.web
import adisp
import brukva
import json
from card import create_cards
import pvp

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
                warlord_proto_id = int(self.get_argument("warlord"))
                if warlord_proto_id not in (119, 120, 121, 122, 123, 124, 125, 126):
                    raise IndexError("invalid warlord_proto_id")
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
            card_proto_levels = [[warlord_proto_id, 1]]+INIT_CARDS
            cards = yield create_cards(userid, card_proto_levels, INIT_MAX_CARD, WAGON_INDEX_GENERAL)
            warlord_card = cards[0]
            warlord_id = warlord_card["id"]

            # init bands
            bands = INIT_BANDS[:]

            for band in bands:
                band["members"][1] = warlord_id
                
            bands[0]["members"][0] = cards[1]["id"]
            bands[0]["members"][3] = cards[2]["id"]

            bands = json.dumps(bands)

            # init items
            items = json.dumps(INIT_ITEMS)

            # wagon
            wagon = json.dumps(INIT_WAGON)

            # create player info
            row_nums = yield util.whdb.runOperation(
                """ INSERT INTO playerInfos
                        (userId, name, warLord, money, inZoneId, lastZoneId, maxCardNum, maxTradeNum, currentBand, 
                            xp, maxXp, ap, maxAp, bands, items, wagonGeneral, wagonTemp, wagonSocial)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                ,(userid, username, warlord_id, INIT_GOLD, 0, INIT_ZONE_ID, INIT_MAX_CARD, INIT_MAX_TRADE, 0
                , INIT_XP, INIT_XP, INIT_AP, INIT_AP, bands, items, wagon, wagon, wagon)
            )

            #reply
            reply = util.new_reply()
            reply["warlord"] = warlord_card
            self.write(json.dumps(reply))
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
            cols = "userId,name,warlord,whcoin,money,inZoneId,lastZoneId,maxCardNum," \
                    "xp,maxXp,lastXpTime,ap,maxAp,lastApTime,currentBand," \
                    "lastFormation,bands,items,wagonGeneral,wagonTemp,wagonSocial,"\
                    "pvpWinStreak,UTC_TIMESTAMP(),tutorialStep"

            sql = "SELECT {} FROM playerInfos WHERE userId=%s".format(cols)
            rows = yield util.whdb.runQuery(
                sql,
                (userid, )
            )
            cols = cols.split(",")
            infos = dict(zip(cols, rows[0]))

            # update playerName to session
            session["playerName"] = infos["name"]
            yield set_session(self, session)

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
                cardsInPackage = [card for card in cards if card["inPackage"]]
                wagonCardNum = len(cards) - len(cardsInPackage)

            except:
                raise Exception("Get cards error. ownerId=%s" % userid)

            # reply
            reply = infos
            reply["error"] = no_error

            #update xp
            oldxp = xp = infos["xp"]
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
                last_xp_time = curr_time
            else:
                t = dt % XP_ADD_DURATION
                reply["xpAddRemain"] = XP_ADD_DURATION - t
                last_xp_time = curr_time - timedelta(seconds = t)
            reply["xp"] = xp

            #update ap
            oldap = ap = infos["ap"]
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
                last_ap_time = curr_time
            else:
                t = dt % AP_ADD_DURATION
                reply["apAddRemain"] = AP_ADD_DURATION - t
                last_ap_time = curr_time - timedelta(seconds = t)
            reply["ap"] = ap

            # update wagon objs count
            rows = yield util.whdb.runQuery(
                """SELECT (SELECT COUNT(*) FROM wagons WHERE userId=%s AND wagonIdx=0),
                        (SELECT COUNT(*) FROM wagons WHERE userId=%s AND wagonIdx=1),
                        (SELECT COUNT(*) FROM wagons WHERE userId=%s AND wagonIdx=2)
                """,
                (userid, userid, userid)
            )
            wagonObjNums = rows[0]
            oldWagonObjNums = [infos["wagonGeneral"], infos["wagonTemp"], infos["wagonSocial"]]
            reply["wagonGeneral"] = wagonObjNums[0]
            reply["wagonTemp"] = wagonObjNums[1]
            reply["wagonSocial"] = wagonObjNums[2]

            # update to db
            if (oldap != ap) or (oldxp != xp) or (wagonObjNums != oldWagonObjNums):
                yield util.whdb.runOperation(
                    """UPDATE playerInfos SET ap=%s, lastApTime=%s, xp=%s, lastXpTime=%s,
                            wagonGeneral=%s, wagonTemp=%s, wagonSocial=%s
                            WHERE userId=%s"""
                    ,(ap, last_ap_time, xp, last_xp_time, wagonObjNums[0], wagonObjNums[1], wagonObjNums[2], userid)
                )

            # pvp
            matched_bands = []
            pvp_remain_time = 0

            key = "pvpFoeBands/%s" % userid
            pipe = util.redis_pipe()
            pipe.get(key)
            pipe.ttl(key)
            pipe_results = yield util.redis_pipe_execute(pipe)
            matched_bands = pipe_results[0]
            
            if matched_bands:
                matched_bands = json.loads(matched_bands)
                pvp_remain_time = pipe_results[1]
            else:
                matched_bands = []

            # 
            reply["tutorialStepIndex"] = reply["tutorialStep"]
            del reply["tutorialStep"]

            # reply
            del reply["lastXpTime"]
            del reply["lastApTime"]
            bands = json.loads(infos["bands"])
            reply["bands"] = [{"index":idx, "formation":band["formation"], "members":band["members"]} for idx, band in enumerate(bands)]
            items = json.loads(infos["items"])
            reply["items"] = [{"id": int(k), "num": v} for k, v in items.iteritems()]
            reply["cards"] = cardsInPackage
            reply["wagonCardNum"] = wagonCardNum
            reply["pvpBands"] = matched_bands
            reply["pvpRemainTime"] = pvp_remain_time
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
            username = session["username"]

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
                ms = set(members)
                ms.discard(None)
                if len(ms) != len(mems_not_none):
                    raise Exception("card entity id repeated")
                member_set |= ms

                db_bands[index] = {"formation":formation, "members":members}

            # check member
            mem_proto_num = len(member_set)
            cols = ["id", "protoId", "level", "skill1Id", "skill1Level", "skill2Id", "skill2Level", "skill3Id", "skill3Level", 
                "hp", "atk", "def", "wis", "agi", "hpExtra", "atkExtra", "defExtra", "wisExtra", "agiExtra", 
                "hpCrystal", "atkCrystal", "defCrystal", "wisCrystal", "agiCrystal"]
            if mem_proto_num:
                rows = yield util.whdb.runQuery(
                    """ SELECT {} FROM cardEntities
                            WHERE ownerId = %s AND id IN ({})""".format(",".join(cols), ",".join(map(str, member_set)))
                    ,(userid,)
                )
                count = len(rows)
                if count != mem_proto_num:
                    raise Exception("May be one or some cards is not yours")

            card_entities = {row[0]:dict(zip(cols, row)) for row in rows}

            # get warlord level and proto
            warlord_level = card_entities[warlord]["level"]
            warload_proto = card_entities[warlord]["protoId"]

            # update pvp band
            pvp_bands = []
            for band in bands:
                pvp_band = {}
                pvp_band["formation"] = band["formation"]
                pvp_cards = []
                for card_entity_id in band["members"]:
                    if card_entity_id == None:
                        pvp_cards.append(None)
                        continue

                    card_entity = card_entities[card_entity_id]
                    hp, atk, dfc, wis, agi, skill1id, sill2id = \
                        map(int, card_tbl.gets(card_entity["protoId"], "maxhp", "maxatk", "maxdef", "maxwis", "maxagi", "skillid1", "skillid2"))
                    card = {}
                    card["protoId"] = card_entity["protoId"]
                    card["level"] = card_entity["level"]
                    card["hp"] = hp
                    card["atk"] = atk
                    card["def"] = dfc
                    card["wis"] = wis
                    card["agi"] = agi
                    card["hpTotal"] = card_entity["hp"] + card_entity["hpExtra"] + card_entity["hpCrystal"]*POINT_PER_CRYSTAL
                    card["atkTotal"] = card_entity["atk"] + card_entity["atkExtra"] + card_entity["atkCrystal"]*POINT_PER_CRYSTAL
                    card["defTotal"] = card_entity["def"] + card_entity["defExtra"] + card_entity["defCrystal"]*POINT_PER_CRYSTAL
                    card["wisTotal"] = card_entity["wis"] + card_entity["wisExtra"] + card_entity["wisCrystal"]*POINT_PER_CRYSTAL
                    card["agiTotal"] = card_entity["agi"] + card_entity["agiExtra"] + card_entity["agiCrystal"]*POINT_PER_CRYSTAL
                    card["skill1Id"] = card_entity["skill1Id"]
                    card["skill1Level"] = card_entity["skill1Level"]
                    card["skill2Id"] = card_entity["skill2Id"]
                    card["skill2Level"] = card_entity["skill2Level"]
                    card["skill3Id"] = card_entity["skill3Id"]
                    card["skill3Level"] = card_entity["skill3Level"]
                    pvp_cards.append(card)

                pvp_band["cards"] = pvp_cards
                pvp_bands.append(pvp_band)

            pvp_score = yield pvp.update_pvp_band(userid, username, warlord_level, warload_proto, pvp_bands)

            # store db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET bands=%s, pvpScore=%s
                        WHERE userId=%s"""
                ,(json.dumps(db_bands), pvp_score, userid)
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
    def post(self):
        try:
            # session
            session = yield find_session(self)
            if not session:
                send_error(self, err_auth)
                return
            user_id = session["userid"]

            # params
            try:
                post_input = json.loads(self.request.body)
                item_id = post_input["itemid"]
                try:
                    targets = post_input["targets"]
                except:
                    targets = []

                if len(targets) > 10:
                    raise Exception("len of targets > 10")
                for t in targets:
                    if not isinstance(t, int):
                        raise Exception("target not int")

            except:
                send_error(self, err_param)
                return;

            # query items info
            rows = yield util.whdb.runQuery(
                """ SELECT items, ap, maxAp, zoneCache, xp, maxXp, lastApTime, lastXpTime, UTC_TIMESTAMP() FROM playerInfos
                        WHERE userId=%s"""
                ,(user_id, )
            )
            row = rows[0]
            items = json.loads(row[0])
            ap = row[1]
            maxAp = row[2]
            zoneCache = row[3]
            xp = row[4]
            maxXp = row[5]
            lastApTime = row[6]
            lastXpTime = row[7]
            currTime = row[8]


            def consumeItem(items, num):
                item_num = items.get(str(item_id), 0)
                remain = item_num - num
                if remain < 0:
                    raise Exception("not enough item")
                items[str(item_id)] = remain
                return remain

            item_id = int(item_id)

            apAddRemain = 0
            xpAddRemain = 0

            # use item
            ## recover all ap
            if item_id == 1: 
                if ap == maxAp:
                    raise Exception("ap full")

                item_num = consumeItem(items, 1)

                yield util.whdb.runOperation(
                    """ UPDATE playerInfos SET items=%s, ap=maxAp
                            WHERE userId=%s"""
                    ,(json.dumps(items), user_id)
                )

            ## recover one hp
            elif item_id == 2:
                if not zoneCache:
                    raise Exception("not in zone")
                    
                if not targets:
                    raise Exception("no targets")

                zoneCache = json.loads(zoneCache)
                bandmems = zoneCache["band"]["members"]

                rows = yield util.whdb.runQuery(
                    """ SELECT hp, hpCrystal, hpExtra, id FROM cardEntities
                        WHERE ownerId=%s AND id IN ({})""".format(",".join((str(t) for t in targets))),
                    (user_id,)
                )
                # target_hps = [sum(row) for row in rows]
                # target_hps = dict(zip(targets, target_hps))
                target_hps = {row[3]:row[0]+row[1]+row[2] for row in rows}
                
                num = 0
                for m in bandmems:
                    if m and m[0] in target_hps and m[1] > 0:
                        full_hp = target_hps[m[0]]
                        if m[1] != full_hp:
                            m[1] = full_hp
                            num += 1

                if num:
                    item_num = consumeItem(items, num)

                    yield util.whdb.runOperation(
                        """ UPDATE playerInfos SET items=%s, zoneCache=%s
                                WHERE userId=%s"""
                        ,(json.dumps(items), json.dumps(zoneCache), user_id)
                    )
                else:
                    raise Exception("no effect")

            ## revive one 
            elif item_id == 3:
                if not zoneCache:
                    raise Exception("not in zone")

                if not targets:
                    raise Exception("no targets")

                zoneCache = json.loads(zoneCache)
                bandmems = zoneCache["band"]["members"]

                rows = yield util.whdb.runQuery(
                    """ SELECT hp, hpCrystal, hpExtra, id FROM cardEntities
                        WHERE ownerId=%s AND id IN ({})""".format(",".join((str(t) for t in targets))),
                    (user_id,)
                )
                # target_hps = [sum(row) for row in rows]
                # target_hps = dict(zip(targets, target_hps))
                target_hps = {row[3]:row[0]+row[1]+row[2] for row in rows}
                
                num = 0
                for m in bandmems:
                    if m and m[0] in target_hps and m[1] == 0:
                        full_hp = target_hps[m[0]]
                        if m[1] != full_hp:
                            m[1] = full_hp
                            num += 1

                if num:
                    item_num = consumeItem(items, num)

                    yield util.whdb.runOperation(
                        """ UPDATE playerInfos SET items=%s, zoneCache=%s
                                WHERE userId=%s"""
                        ,(json.dumps(items), json.dumps(zoneCache), user_id)
                    )
                else:
                    raise Exception("no effect")

            ## recover all hp
            elif item_id == 4:
                if not zoneCache:
                    raise Exception("not in zone")

                zoneCache = json.loads(zoneCache)
                bandmems = zoneCache["band"]["members"]

                targets = [m[0] for m in bandmems if m]

                rows = yield util.whdb.runQuery(
                    """ SELECT hp, hpCrystal, hpExtra, id FROM cardEntities
                        WHERE ownerId=%s AND id IN ({})""".format(",".join((str(t) for t in targets))),
                    (user_id,)
                )
                # target_hps = [sum(row) for row in rows]
                # target_hps = dict(zip(targets, target_hps))
                target_hps = {row[3]:row[0]+row[1]+row[2] for row in rows}
                
                hp_added = False
                for m in bandmems:
                    if m and m[0] in target_hps and m[1] > 0:
                        full_hp = target_hps[m[0]]
                        if m[1] != full_hp:
                            m[1] = full_hp
                            hp_added = True

                if hp_added:
                    item_num = consumeItem(items, 1)

                    yield util.whdb.runOperation(
                        """ UPDATE playerInfos SET items=%s, zoneCache=%s
                                WHERE userId=%s"""
                        ,(json.dumps(items), json.dumps(zoneCache), user_id)
                    )
                else:
                    raise Exception("no effect")

            ## recover one xp
            elif item_id == 10:
                try:
                    allout = post_input["allout"]
                except:
                    allout = False

                if xp == maxXp:
                    raise Exception("xp full")

                if allout:
                    dxp = maxXp - xp
                else:
                    dxp = 1

                count = post_input.get("count", 0)
                count = min(maxXp - xp, count)
                if count > 1:
                    dxp = count

                item_num = consumeItem(items, dxp)
                yield util.whdb.runOperation(
                    """ UPDATE playerInfos SET items=%s, xp=xp+%s
                            WHERE userId=%s"""
                    ,(json.dumps(items), dxp, user_id)
                )

                xp += dxp

                if xp == maxXp:
                    xpAddRemain = 0
                else:
                    dt = currTime - lastXpTime
                    dt = int(dt.total_seconds())
                    xpAddRemain = XP_ADD_DURATION - dt % XP_ADD_DURATION

            ## recover all xp
            elif item_id == 11:
                if xp == maxXp:
                    raise Exception("xp full")

                item_num = consumeItem(items, 1)
                yield util.whdb.runOperation(
                    """ UPDATE playerInfos SET items=%s, xp=maxXp
                            WHERE userId=%s"""
                    ,(json.dumps(items), user_id)
                )

            ## recover AP small
            elif item_id == 22:
                if ap == maxAp:
                    raise Exception("ap full")

                ap += 5

                if ap >= maxAp:
                    ap = maxAp

                item_num = consumeItem(items, 1)

                yield util.whdb.runOperation(
                    """ UPDATE playerInfos SET items=%s, ap=%s
                            WHERE userId=%s"""
                    ,(json.dumps(items), ap, user_id)
                )

                if ap == maxAp:
                    apAddRemain = 0
                else:
                    dt = currTime - lastApTime
                    dt = int(dt.total_seconds())
                    apAddRemain = AP_ADD_DURATION - dt % AP_ADD_DURATION
            
            # reply
            reply = util.new_reply()
            reply["itemId"] = int(item_id)
            reply["itemNum"] = item_num
            reply["ap"] = ap
            reply["apAddRemain"] = apAddRemain
            reply["xp"] = xp
            reply["xpAddRemain"] = xpAddRemain
            self.write(json.dumps(reply))
            
        except:
            send_internal_error(self)
        finally:
            self.finish()


class GetTime(tornado.web.RequestHandler):
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
            

            # query
            rows = yield util.whdb.runQuery(
                """ SELECT xp,maxXp,lastXpTime,ap,maxAp,lastApTime, UTC_TIMESTAMP() FROM playerInfos
                    WHERE userId=%s""",
                (userid,)
            )

            row = rows[0]
            old_xp = xp = row[0]
            max_xp = row[1]
            last_xp_time = row[2]
            old_ap = ap = row[3]
            max_ap = row[4]
            last_ap_time = row[5]
            curr_time = row[6]

            #update xp
            if not last_xp_time:
                last_xp_time = datetime(2013, 1, 1)
            dt = curr_time - last_xp_time
            dt = int(dt.total_seconds())
            dxp = dt // XP_ADD_DURATION
            if dxp:
                xp = min(max_xp, xp + dxp)
            if xp == max_xp:
                xp_add_remain = 0
                last_xp_time = curr_time
            else:
                t = dt % XP_ADD_DURATION
                xp_add_remain = XP_ADD_DURATION - t
                last_xp_time = curr_time - timedelta(seconds = t)

            #update ap
            if not last_ap_time:
                last_ap_time = datetime(2013, 1, 1)
            dt = curr_time - last_ap_time
            dt = int(dt.total_seconds())
            dap = dt // AP_ADD_DURATION
            if dap:
                ap = min(max_ap, ap + dap)
            if ap == max_ap:
                ap_add_remain = 0
                last_ap_time = curr_time
            else:
                t = dt % AP_ADD_DURATION
                ap_add_remain = AP_ADD_DURATION - t
                last_ap_time = curr_time - timedelta(seconds = t)

            # update db
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET ap=%s, lastApTime=%s, xp=%s, lastXpTime=%s
                        WHERE userId=%s"""
                ,(ap, last_ap_time, xp, last_xp_time, userid)
            )

            # pvp remain time
            key = "pvpFoeBands/%s" % userid
            pvp_remain_time = yield util.redis().ttl(key)
            if not pvp_remain_time:
                pvp_remain_time = 0

            #reply
            reply = util.new_reply()
            reply["xp"] = xp
            reply["xpAddRemain"] = xp_add_remain;
            reply["ap"] = ap
            reply["apAddRemain"] = ap_add_remain;
            reply["pvpRemainTime"] = pvp_remain_time
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetTutorialStep(tornado.web.RequestHandler):
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

            # param
            post_input = json.loads(self.request.body)
            tutorial_step = post_input["tutorialStepIndex"]

            # update
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET tutorialStep=%s WHERE userId=%s"""
                ,(tutorial_step, userid)
            )

            # reply
            reply = util.new_reply()
            reply["tutorialStepIndex"] = tutorial_step
            self.write(json.dumps(reply))
        except:
            send_internal_error(self)
        finally:
            self.finish()


class SetName(tornado.web.RequestHandler):
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

            # param
            post_input = json.loads(self.request.body)
            name = post_input["name"]

            # update
            yield util.whdb.runOperation(
                """UPDATE playerInfos SET name=%s WHERE userId=%s"""
                ,(name, userid)
            )

            session["playerName"] = name
            yield set_session(self, session)

            # reply
            reply = util.new_reply()
            reply["name"] = name.encode("utf-8")
            js = json.dumps(reply, ensure_ascii=False)
            self.write(js)
        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/player/create", Create),
    (r"/whapi/player/getinfo", GetInfo),
    (r"/whapi/player/setband", SetBand),
    (r"/whapi/player/useitem", UseItem),
    (r"/whapi/player/time", GetTime),
    (r"/whapi/player/settutorialstepindex", SetTutorialStep),
    (r"/whapi/player/setname", SetName),
]