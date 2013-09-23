package main

import (
	//_ "github.com/go-sql-driver/mysql"
	//"github.com/golang/glog"
	"encoding/json"
	"fmt"
	"github.com/henyouqian/lwutil"
	"net/http"
	"strconv"
	"time"
)

func instanceList(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

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
			v.TimesRestrict,
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

	//in
	var in struct {
		InstanceID uint32
	}
	err := lwutil.DecodeRequestBody(r, &in)
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
	row := whDB.QueryRow("SELECT bands, inZoneId FROM playerInfos WHERE userId=?", session.Userid)
	var bandsJs []byte
	var inZoneId uint32
	err = row.Scan(&bandsJs, &inZoneId)
	lwutil.CheckError(err, "")

	//parse band
	type Band struct {
		Formation uint32
		Members   []uint32
	}
	var bands []Band
	err = json.Unmarshal(bandsJs, &bands)
	lwutil.CheckError(err, "")

	if in.BandIdx >= uint32(len(bands)) {
		lwutil.SendError("err_input", fmt.Sprintf("invalid band index:%d", in.BandIdx))
	}

	//check zone id
	if inZoneId != 0 {
		lwutil.SendError("err_in_zone", "alread in zone")
	}

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
	_ = inst

	//some check...

	//

	//out
	type OutObj []uint32

	type OutEvent struct {
		X           uint32 `json:"x"`
		Y           uint32 `json:"y"`
		StartDialog uint32 `json:"startDialog"`
		EndDialog   uint32 `json:"endDialog"`
		Obj         int32  `json:"obj"`
	}

	type OutBandMember struct {
		Id uint32 `json:"id"`
		Hp uint32 `json:"hp"`
	}
	type OutBand struct {
		Formation uint32          `json:"formation"`
		Members   []OutBandMember `json:"members"`
	}

	type OutVec2 struct {
		X uint32 `json:"x"`
		Y uint32 `json:"y"`
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
		Band             []OutBand  `json:"band"`
		EnterDialogue    uint32     `json:"enterDialogue"`
		CompleteDialogue uint32     `json:"completeDialogue"`
		PlayerRank       uint32     `json:"playerRank"`
		PlayerScore      uint32     `json:"playerScore"`
		Xp               uint32     `json:"xp"`
		XpAddRemain      uint32     `json:"xpAddRemain"`
		Whcoin           uint32     `json:"whcoin"`
		Temp             interface{}
	}
	out := Out{
		Error:            "",
		ZoneId:           0,
		StartPos:         OutVec2{0, 0},
		GoalPos:          OutVec2{0, 0},
		CurrPos:          OutVec2{0, 0},
		RedCase:          0,
		GoldCase:         0,
		Objs:             []OutObj{{2, 3, 4}, {4, 3, 2}},
		Events:           []OutEvent{{}, {}},
		Band:             []OutBand{{Members: []OutBandMember{}}},
		EnterDialogue:    0,
		CompleteDialogue: 0,
		PlayerRank:       0,
		PlayerScore:      0,
		Xp:               0,
		XpAddRemain:      0,
		Whcoin:           0,
		Temp:             bands,
	}
	lwutil.WriteResponse(w, out)
}

func regInstance() {
	http.Handle("/whapi/instance/list", lwutil.ReqHandler(instanceList))
	http.Handle("/whapi/instance/zonelist", lwutil.ReqHandler(instanceZoneList))
	http.Handle("/whapi/instance/enterzone", lwutil.ReqHandler(instanceEnterZone))
}
