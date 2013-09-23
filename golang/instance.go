package main

import (
	//_ "github.com/go-sql-driver/mysql"
	//"encoding/json"
	//"fmt"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
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
		inst := Instance{
			v.Id,
			v.Name,
			v.Type,
			v.LevelRestrict,
			v.ZoneRestrict,
			v.TimesRestrict,
			v.DisplayOrder,
			v.OpenDate,
			v.CloseDate,
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

	for _, v := range tblInstanceZoneList {
		if v.InstanceID == in.InstanceID {
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
	out := Out{0, zones}
	lwutil.WriteResponse(w, out)
}

func regInstance() {
	http.Handle("/whapi/instance/list", lwutil.ReqHandler(instanceList))
	http.Handle("/whapi/instance/zonelist", lwutil.ReqHandler(instanceZoneList))
}
