package main

import (
	//_ "github.com/go-sql-driver/mysql"
	"encoding/json"
	"fmt"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"strconv"
	"time"
)

type TimesRestrict struct {
	Times   uint32
	YearDay uint32
}

func instanceList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	type Instance struct {
		Id            uint32 `json:"id"`
		Name          string `json:"name"`
		Type          uint32 `json:"type"`
		LevelRestrict uint32 `json:"levelRestrict"`
		ZoneRestrict  uint32 `json:"zoneRestrict"`
		TimesRestrict uint32 `json:"timesRestrict"`
		DisplayOrder  uint32 `json:"displayOrder"`
		OpenDate      string `json:"openDate"`
		CloseDate     string `json:"closeDate"`
		CoolDown      uint32 `json:"coolDown"`
		RemainTimes   uint32 `json:"remainTimes"`
	}

	today := uint32(lwutil.GetRedisTime().YearDay())
	instList := make([]Instance, 0, 8)
	for _, v := range tblInstanceList {
		openDate := ""
		closeDate := ""
		if v.OpenDate != "0" {
			t, err := time.ParseInLocation("2006-01-02", v.OpenDate, time.Local)
			lwutil.CheckError(err, "")
			openDate = fmt.Sprintf("%d月%d日", t.Month(), t.Day())
		}
		if v.CloseDate != "0" {
			t, err := time.ParseInLocation("2006-01-02", v.CloseDate, time.Local)
			lwutil.CheckError(err, "")
			closeDate = fmt.Sprintf("%d月%d日", t.Month(), t.Day())
		}

		timesRemain := uint32(0)

		var timesRestrict TimesRestrict
		key := fmt.Sprintf("instTimesRst/user=%d&inst=%d", session.UserId, v.Id)
		exist, err := lwutil.GetKv(key, &timesRestrict, rc)
		if !exist {
			timesRemain = v.TimesRestrict
		} else {
			lwutil.CheckError(err, "")
			if today != timesRestrict.YearDay {
				timesRemain = v.TimesRestrict
			} else {
				timesRemain = v.TimesRestrict - timesRestrict.Times
				if timesRemain < 0 {
					timesRemain = 0
				}
			}
		}

		inst := Instance{
			v.Id,
			v.Name,
			v.Type,
			v.LevelRestrict,
			v.ZoneRestrict,
			v.TimesRestrict,
			v.DisplayOrder,
			openDate,
			closeDate,
			v.CoolDown,
			timesRemain,
		}
		instList = append(instList, inst)
	}

	//out
	type Out struct {
		Instance []Instance `json:"instance"`
	}
	out := Out{instList}
	lwutil.WriteResponse(w, out)
}

func instanceZoneList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//in
	var in struct {
		InstanceID uint32
	}
	err = lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	type Zone struct {
		ZoneId        uint32   `json:"zoneId"`
		ResourceId    uint32   `json:"resourceId"`
		Name          string   `json:"name"`
		Comment       string   `json:"comment"`
		Difficulty    uint32   `json:"difficulty"`
		LevelRestrict uint32   `json:"levelRestrict"`
		XpCost        uint32   `json:"xpCost"`
		ZoneNo        uint32   `json:"zoneNo"`
		NextZoneId    uint32   `json:"nextZoneId"`
		Price         uint32   `json:"price"`
		BgmId         uint32   `json:"bgmId"`
		DropCardIds   []uint32 `json:"dropCardIds"`
		DropItemIds   []uint32 `json:"dropItemIds"`
	}
	zones := make([]Zone, 0, 8)

	lastZone := uint32(0)

	key := fmt.Sprintf("lastInstZoneId/user=%d&inst=%d", session.UserId, in.InstanceID)
	_, err = lwutil.GetKv(key, &lastZone, rc)
	lwutil.CheckError(err, "")
	for _, v := range tblInstanceZoneList {
		if v.InstanceID == in.InstanceID {
			if lastZone == 0 {
				lastZone = v.ZoneId
			}
			var zone Zone
			zone.ZoneId = v.ZoneId
			zone.ResourceId = v.ResourceId
			zone.Name = v.Name
			zone.Comment = v.Comment
			zone.Difficulty = v.Difficulty
			zone.LevelRestrict = v.LevelRestrict
			zone.XpCost = v.XpCost
			zone.ZoneNo = v.ZoneNo
			zone.NextZoneId = v.NextZoneId
			zone.Price = v.Price
			zone.BgmId = v.BgmId
			zone.DropCardIds = []uint32{v.DropCard1Id, v.DropCard2Id, v.DropCard3Id, v.DropCard4Id, v.DropCard5Id, v.DropCard6Id}
			zone.DropItemIds = []uint32{v.DropItem1Id, v.DropItem2Id, v.DropItem3Id, v.DropItem4Id, v.DropItem5Id, v.DropItem6Id}
			for ii, vv := range zone.DropCardIds {
				if vv == 0 {
					zone.DropCardIds = zone.DropCardIds[:ii]
					break
				}
			}
			for ii, vv := range zone.DropItemIds {
				if vv == 0 {
					zone.DropItemIds = zone.DropItemIds[:ii]
					break
				}
			}
			zones = append(zones, zone)
		}
	}

	// out
	type Out struct {
		LastZone     uint32 `json:"lastZone"`
		InstanceZone []Zone `json:"instanceZone"`
	}
	out := Out{lastZone, zones}
	lwutil.WriteResponse(w, out)
}

func instanceEnterZone(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//input
	var in struct {
		ZoneId  uint32
		BandIdx uint32
	}
	err = lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")

	//get player info
	row := whDB.QueryRow("SELECT bands, inZoneId, xp, maxXp, lastXpTime, whCoin, UTC_TIMESTAMP(), warLord FROM playerInfos WHERE userId=?", session.UserId)
	var bandsJs []byte
	var inZoneId uint32
	var xp uint32
	var maxXp uint32
	var lastXpTimeStr string
	var whCoin uint32
	var nowStr string
	var warlord uint32
	err = row.Scan(&bandsJs, &inZoneId, &xp, &maxXp, &lastXpTimeStr, &whCoin, &nowStr, &warlord)
	lwutil.CheckError(err, "")

	lastXpTime, err := time.ParseInLocation("2006-01-02 15:04:05", lastXpTimeStr, time.UTC)
	lwutil.CheckError(err, "")
	now, err := time.ParseInLocation("2006-01-02 15:04:05", nowStr, time.UTC)
	lwutil.CheckError(err, "")

	//check zone id
	//if inZoneId != 0 {
	//	lwutil.SendError("err_in_zone", "alread in zone")
	//}

	//get warlord info
	row = whDB.QueryRow("SELECT level FROM cardEntities WHERE id=?", warlord)
	var level uint32
	err = row.Scan(&level)
	lwutil.CheckError(err, "")

	//parse band
	var bands []Band
	err = json.Unmarshal(bandsJs, &bands)
	lwutil.CheckError(err, "")

	if in.BandIdx >= uint32(len(bands)) {
		lwutil.SendError("err_input", fmt.Sprintf("invalid band index:%d", in.BandIdx))
	}

	currBand := bands[in.BandIdx]

	//instance zone data
	instZone, ok := tblInstanceZone[strconv.FormatUint(uint64(in.ZoneId), 10)]
	if !ok {
		lwutil.SendError("err_input", fmt.Sprintf("invalid zoneid:%d", in.ZoneId))
	}

	//instance data
	inst, ok := tblInstance[strconv.FormatUint(uint64(instZone.InstanceID), 10)]
	if !ok {
		lwutil.SendError("", fmt.Sprintf("invalid instanceId:%d", instZone.InstanceID))
	}

	//update xp
	if lastXpTime.Unix() > now.Unix() {
		lastXpTime = now
	}
	dt := now.Sub(lastXpTime)
	dSec := int32(dt.Seconds())
	dxp := int32(dSec / XP_ADD_DURATION)
	if dxp > 0 {
		xp = uint32(lwutil.Min(int64(maxXp), int64(int32(xp)+dxp)))
	}
	if xp == maxXp {
		lastXpTime = now
	} else {
		t := dSec % XP_ADD_DURATION
		lastXpTime = now.Add(time.Duration(-t) * time.Second)
	}
	xpAddRemain := XP_ADD_DURATION - (dSec % XP_ADD_DURATION)

	//check and consume xp
	if xp < instZone.XpCost {
		lwutil.SendError("err_xp_not_enough", fmt.Sprintf("xp=%d, xpcost=%d", xp, instZone.XpCost))
	}
	xp -= instZone.XpCost
	xp = uint32(lwutil.Truncate(int64(xp), int64(0), int64(maxXp)))

	if xp == maxXp {
		xpAddRemain = 0
	}

	//some instance restrict checking...
	// times restrict
	if inst.TimesRestrict > 0 {
		var timesRestrict TimesRestrict
		key := fmt.Sprintf("instTimesRst/user=%d&inst=%d", session.UserId, inst.Id)
		exist, err := lwutil.GetKv(key, &timesRestrict, rc)
		lwutil.CheckError(err, "")

		canPlay := func() bool {
			today := uint32(lwutil.GetRedisTime().YearDay())
			if exist {
				if timesRestrict.YearDay == today {
					if timesRestrict.Times >= inst.TimesRestrict {
						return false
					} else {
						timesRestrict.Times++
					}
				} else {
					timesRestrict.YearDay = today
					timesRestrict.Times = 1
				}
			} else {
				timesRestrict.YearDay = today
				timesRestrict.Times = 1
			}
			return true
		}()

		if !canPlay {
			if whCoin < instZone.Price {
				lwutil.SendError("err_times_restrict", "")
			}
			whCoin -= instZone.Price
		}

		lwutil.SetKv(key, &timesRestrict, rc)
	}

	// level restrict
	if instZone.LevelRestrict != 0 && level < instZone.LevelRestrict {
		lwutil.SendError("err_level_restrict", "")
	}

	//gen cache
	cache, err := genCache(in.ZoneId, true, session.UserId, currBand)
	lwutil.CheckError(err, "")

	//out
	// out obj
	type OutObj [3]int32
	outObjs := make([]OutObj, len(cache.Objs))
	i := 0
	for k, v := range cache.Objs {
		var x, y int32
		fmt.Sscanf(k, "%d,%d", &x, &y)
		outObjs[i] = [3]int32{x, y, v}
		i++
	}

	// out event
	type OutEvent struct {
		X           uint32 `json:"x"`
		Y           uint32 `json:"y"`
		StartDialog uint32 `json:"startDialog"`
		EndDialog   uint32 `json:"endDialog"`
		Obj         int32  `json:"obj"`
	}
	outEvents := make([]OutEvent, 0, 8)

	for xyStr, eventId := range cache.Events {
		tblRow, ok := tblEvent[strconv.FormatUint(uint64(eventId), 10)]
		if !ok {
			lwutil.SendError("", fmt.Sprintf("invalid eventId: %d", eventId))
		}

		var outEvent OutEvent
		fmt.Sscanf(xyStr, "%d,%d", &outEvent.X, &outEvent.Y)
		outEvent.StartDialog = tblRow.StartdialogueID
		outEvent.EndDialog = tblRow.OverdialogueID

		//
		if tblRow.MonsterID != 0 {
			outEvent.Obj = int32(-tblRow.MonsterID)
		} else if tblRow.Item1ID != 0 {
			itemMap := map[uint32]uint32{18: 4, 19: 5, 20: 2, 21: 3}
			obj, ok := itemMap[tblRow.Item1ID]
			if !ok {
				lwutil.SendError("", fmt.Sprintf("invalid Item1ID: %d", tblRow.Item1ID))
			}
			outEvent.Obj = int32(obj)
		}

		outEvents = append(outEvents, outEvent)
	}

	//update db
	cacheJs, err := json.Marshal(cache)
	lwutil.CheckError(err, "")
	_, err = whDB.Exec(`UPDATE playerInfos SET zoneCache=?, inZoneId=?, currentBand=?, xp=?, lastXpTime=?, whCoin=?
                WHERE userid=?`, cacheJs, in.ZoneId, in.BandIdx, xp, lastXpTime, whCoin, session.UserId)
	lwutil.CheckError(err, "")

	// out band
	type OutBandMember struct {
		Id uint64 `json:"id"`
		Hp uint32 `json:"hp"`
	}

	type OutBand struct {
		Formation uint32          `json:"formation"`
		Members   []OutBandMember `json:"members"`
	}
	var outband OutBand
	outband.Formation = cache.Band.Formation
	for _, mem := range cache.Band.Members {
		switch mem := mem.(type) {
		case [2]uint64:
			outband.Members = append(outband.Members, OutBandMember{mem[0], uint32(mem[1])})
		}
	}

	type OutVec2 struct {
		X uint32 `json:"x"`
		Y uint32 `json:"y"`
	}

	mapRow, ok := tblMap[strconv.Itoa(int(in.ZoneId))]
	if !ok {
		lwutil.SendError("", fmt.Sprintf("no map in tblMaps: zoneId=%d", in.ZoneId))
	}

	type Out struct {
		Error            string     `json:"error"`
		ZoneId           uint32     `json:"zoneId"`
		StartPos         OutVec2    `json:"startPos"`
		GoalPos          OutVec2    `json:"goalPos"`
		CurrPos          OutVec2    `json:"currPos"`
		RedCase          uint32     `json:"redCase"`
		GoldCase         uint32     `json:"goldCase"`
		Objs             []OutObj   `json:"objs"`
		Events           []OutEvent `json:"events"`
		Band             OutBand    `json:"band"`
		EnterDialogue    uint32     `json:"enterDialogue"`
		CompleteDialogue uint32     `json:"completeDialogue"`
		PlayerRank       uint32     `json:"playerRank"`
		PlayerScore      uint32     `json:"playerScore"`
		Xp               uint32     `json:"xp"`
		XpAddRemain      uint32     `json:"xpAddRemain"`
		Whcoin           uint32     `json:"whcoin"`
		BgmId            uint32     `json:"bgmId"`
		ResourceId       uint32     `json:"resourceId"`
		BattleBgId       string     `json:"battleBgId"`
	}
	out := Out{
		Error:            "",
		ZoneId:           cache.ZoneId,
		StartPos:         OutVec2{cache.StartPos[0], cache.StartPos[1]},
		GoalPos:          OutVec2{cache.GoalPos[0], cache.GoalPos[1]},
		CurrPos:          OutVec2{cache.CurrPos[0], cache.CurrPos[1]},
		RedCase:          cache.RedCase,
		GoldCase:         cache.GoldCase,
		Objs:             outObjs,
		Events:           outEvents,
		Band:             outband,
		EnterDialogue:    mapRow.EnterzonerdialogueID,
		CompleteDialogue: mapRow.CompletezonedialogueID,
		PlayerRank:       0,
		PlayerScore:      0,
		Xp:               xp,
		XpAddRemain:      uint32(xpAddRemain),
		Whcoin:           whCoin,
		BgmId:            mapRow.BgmID,
		ResourceId:       mapRow.ResourceId,
		BattleBgId:       mapRow.BattleBgId,
	}
	lwutil.WriteResponse(w, out)
}

func regInstance() {
	http.Handle("/whapi/instance/list", lwutil.ReqHandler(instanceList))
	http.Handle("/whapi/instance/zonelist", lwutil.ReqHandler(instanceZoneList))
	http.Handle("/whapi/instance/enterzone", lwutil.ReqHandler(instanceEnterZone))
}
