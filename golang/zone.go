package main

import (
	"encoding/json"
	"fmt"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"io/ioutil"
	"math/rand"
	"os"
	"strconv"
	"strings"
)

const (
	TILE_ALL   = 4 //tile index in tiled(the editor), gen item or monster
	TILE_ITEM  = 5 //tile index which generate item only
	TILE_MON   = 6 //tile index which generate monster only
	TILE_START = 2 //start tile
	TILE_GOAL  = 3 //goal tile
)

var (
	zoneDatas map[uint32]map[string]uint8
)

func init() {
	parseMaps()
}

func parseMaps() error {
	type Layer struct {
		Name string
		Data []uint8
	}
	type Zone struct {
		Width  uint32
		Height uint32
		Layers []Layer
	}

	zoneDatas = make(map[uint32]map[string]uint8)

	dir := "../data/map"
	files, _ := ioutil.ReadDir(dir)
	for _, f := range files {
		s := strings.Split(f.Name(), ".")
		if s[1] == "json" {
			filepath := dir + "/" + f.Name()
			pf, err := os.Open(filepath)
			if err != nil {
				return lwutil.NewErr(err)
			}
			defer pf.Close()
			dec := json.NewDecoder(pf)
			var zone Zone
			dec.Decode(&zone)

			//
			zoneData := make(map[string]uint8)
			for _, layer := range zone.Layers {
				if layer.Name == "event" {
					for i, v := range layer.Data {
						if v != 0 {
							x := uint32(i) % zone.Width
							y := uint32(i) / zone.Height
							zoneData[fmt.Sprintf("%d,%d", x, y)] = uint8(v)
						}
					}
					zoneId, err := strconv.Atoi(s[0])
					lwutil.PanicIfError(err)
					zoneDatas[uint32(zoneId)] = zoneData
					break
				}
			}
		}
	}
	return nil
}

func getZoneData(zoneid uint32) (map[string]uint8, error) {
	r, ok := zoneDatas[zoneid]
	if !ok {
		return nil, lwutil.NewErrStr(fmt.Sprintf("invalid zoneid: %d", zoneid))
	}
	return r, nil
}

type BandCache struct {
	Formation uint32
	Members   [][2]uint64
}

type zoneCache struct {
	ZoneId    uint32           `json:"zoneId"`
	Objs      map[string]int32 `json:"objs"`
	StartPos  [2]uint32        `json:"startPos"`
	GoalPos   [2]uint32        `json:"goalPos"`
	CurrPos   [2]uint32        `json:"currPos"`
	LastPos   [2]uint32        `json:"lastPos"`
	RedCase   uint32           `json:"redCase"`
	GoldCase  uint32           `json:"goldCase"`
	MonGrpId  int32            `json:"monGrpId"`
	Events    map[string]int32 `json:"events"`
	Band      BandCache        `json:"band"`
	CatchMons []uint32         `json:"catchMons"`
}

func genCache(zoneid uint32, isLastZone bool, userId uint64, band Band) (*zoneCache, error) {
	zoneData, err := getZoneData(zoneid)
	if err != nil {
		return nil, lwutil.NewErr(err)
	}
	mapRow, ok := tblMap[strconv.Itoa(int(zoneid))]
	if !ok {
		return nil, lwutil.NewErrStr(fmt.Sprintf("no map in tblMaps: zoneId=%d", zoneid))
	}

	//weighted rand
	rand1all := newWeightedRandom(1.0, mapRow.ItemProb, mapRow.MonsterProb, mapRow.EventProb, mapRow.PvpProb)
	rand1item := newWeightedRandom(1.0, mapRow.ItemProb+mapRow.MonsterProb, 0, mapRow.EventProb, mapRow.PvpProb)
	rand1mon := newWeightedRandom(1.0, 0, mapRow.ItemProb+mapRow.MonsterProb, mapRow.EventProb, mapRow.PvpProb)

	rand2item := newWeightedRandom(1.0, mapRow.WoodProb, mapRow.RedCaseProb, mapRow.GoldCaseProb, mapRow.LittleGoldProb, mapRow.BigGoldProb)

	//monster group
	monGrpIdsTmp := []uint32{mapRow.Monster1ID, mapRow.Monster2ID, mapRow.Monster3ID, mapRow.Monster4ID, mapRow.Monster5ID,
		mapRow.Monster6ID, mapRow.Monster7ID, mapRow.Monster8ID, mapRow.Monster9ID, mapRow.Monster10ID}
	monGrpIds := make([]uint32, 0, len(monGrpIdsTmp))
	for _, monGrpId := range monGrpIds {
		if monGrpId != 0 {
			monGrpIds = append(monGrpIds, monGrpId)
		}
	}

	var out zoneCache
	out.Objs = make(map[string]int32)
	out.Events = make(map[string]int32)

	//objs
	for tileKey, v := range zoneData {
		var randIdx uint32
		switch v {
		case TILE_ALL:
			randIdx = rand1all.get()
		case TILE_ITEM:
			randIdx = rand1item.get()
		case TILE_MON:
			randIdx = rand1mon.get()
		case TILE_START:
			fmt.Sscanf(tileKey, "%d,%d", &(out.StartPos[0]), &(out.StartPos[1]))
			continue
		case TILE_GOAL:
			fmt.Sscanf(tileKey, "%d,%d", &(out.GoalPos[0]), &(out.GoalPos[1]))
			continue
		default:
			if v > 10 && v <= 20 {
				evtMapRow, ok := tblMapEvent[fmt.Sprintf("%d,%d", zoneid, v)]
				if !ok {
					lwutil.SendError("", fmt.Sprintf("mapEvent not found:mapId=%d, tileValue=%d", zoneid, v))
				}
				eventId := evtMapRow.EventId

				evtRow, ok := tblEvent[strconv.Itoa(int(eventId))]
				if !ok {
					lwutil.SendError("", fmt.Sprintf("evnet not found:eventId=%d", eventId))
				}

				if isLastZone || evtRow.Repeat != 0 {
					out.Events[tileKey] = int32(eventId)
				}
			}

		}

		switch randIdx {
		case 0: //case or gold
			itemType := rand2item.get() + 1 //itemtype from 1 to 5
			out.Objs[tileKey] = int32(itemType)
		case 1: //battle
			n := len(monGrpIds)
			if n > 0 {
				grpId := monGrpIds[rand.Intn(n)]
				out.Objs[tileKey] = -int32(grpId)
			}
		case 2: //event
			//do nothing now
		case 3: //pvp
			out.Objs[tileKey] = 6
		}

	}

	//band
	var bandMemberIdsStr []string
	for _, v := range band.Members {
		if v != 0 {
			bandMemberIdsStr = append(bandMemberIdsStr, strconv.FormatUint(v, 10))
		}
	}
	sql := fmt.Sprintf(`SELECT id, hp, hpCrystal, hpExtra FROM cardEntities
        WHERE id IN (` + strings.Join(bandMemberIdsStr, ",") + `) AND ownerId=?`)
	rows, err := whDB.Query(sql, userId)
	lwutil.CheckError(err, "")
	var members [][2]uint64
	for rows.Next() {
		var (
			id        uint64
			hp        uint32
			hpCrystal uint32
			hpExtra   uint32
		)
		if err := rows.Scan(&id, &hp, &hpCrystal, &hpExtra); err != nil {
			lwutil.CheckError(err, "")
		}
		members = append(members, [2]uint64{id, uint64(hp + hpCrystal + hpExtra)})
	}
	lwutil.CheckError(rows.Err(), "")
	out.Band = BandCache{band.Formation, members}

	//out
	out.ZoneId = zoneid
	out.CurrPos = out.StartPos
	out.LastPos = out.StartPos
	out.MonGrpId = -1
	//out.Events =

	return &out, nil
}

func regZone() {

}
