package main

import (
	"encoding/json"
	"fmt"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"io/ioutil"
	"math"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
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

//func addItems(items map[string]uint32) {

//}

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
	Formation uint32        `json:"formation"`
	Members   []interface{} `json:"members"`
}

type zoneCache struct {
	ZoneId    uint32           `json:"zoneId"`
	Objs      map[string]int32 `json:"objs"`
	StartPos  [2]int32         `json:"startPos"`
	GoalPos   [2]int32         `json:"goalPos"`
	CurrPos   [2]int32         `json:"currPos"`
	RedCase   uint32           `json:"redCase"`
	GoldCase  uint32           `json:"goldCase"`
	MonGrpId  uint32           `json:"monGrpId"`
	Events    map[string]int32 `json:"events"`
	Band      BandCache        `json:"band"`
	CatchMons []uint32         `json:"catchMons"`
}

func genCache(zoneid uint32, isLastZone bool, userId uint32, band Band) (*zoneCache, error) {
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
	rand1item := newWeightedRandom(1.0, mapRow.OnlyItemProb, 0, mapRow.EventProb, mapRow.PvpProb)
	rand1mon := newWeightedRandom(1.0, 0, mapRow.OnlyMonsterProb, mapRow.EventProb, mapRow.PvpProb)

	rand2item := newWeightedRandom(1.0, mapRow.WoodProb, mapRow.TreasureProb, mapRow.ChestProb, mapRow.LittleGoldProb, mapRow.BigGoldProb)

	//monster group
	monGrpIdsTmp := []uint32{mapRow.Monster1ID, mapRow.Monster2ID, mapRow.Monster3ID, mapRow.Monster4ID, mapRow.Monster5ID,
		mapRow.Monster6ID, mapRow.Monster7ID, mapRow.Monster8ID, mapRow.Monster9ID, mapRow.Monster10ID}
	monGrpIds := make([]uint32, 0, len(monGrpIdsTmp))
	for _, monGrpId := range monGrpIdsTmp {
		if monGrpId != 0 {
			monGrpIds = append(monGrpIds, monGrpId)
		}
	}

	var out zoneCache
	out.Objs = make(map[string]int32)
	out.Events = make(map[string]int32)

	//objs
	for tileKey, v := range zoneData {
		randIdx := int32(-1)
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
					lwutil.SendError("", fmt.Sprintf("event not found:eventId=%d", eventId))
				}

				if isLastZone || evtRow.Repeat != 0 {
					out.Events[tileKey] = int32(eventId)
				}
			}

		}

		switch randIdx {
		case 0: //case or gold
			r := rand2item.get()
			if r >= 0 {
				itemType := r + 1 //itemtype from 1 to 5
				out.Objs[tileKey] = int32(itemType)
			}
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
	memMap := make(map[uint64]uint32)
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
		memMap[id] = hp + hpCrystal + hpExtra
	}
	lwutil.CheckError(rows.Err(), "")

	//
	var members []interface{}
	for _, memid := range band.Members {
		if memid != 0 {
			members = append(members, [2]uint64{memid, uint64(memMap[memid])})
		} else {
			members = append(members, nil)
		}
	}

	out.Band = BandCache{band.Formation, members}

	//out
	out.ZoneId = zoneid
	out.CurrPos = out.StartPos
	out.MonGrpId = 0

	return &out, nil
}

func zoneMove(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//*in
	var in [][2]int32
	err = lwutil.DecodeRequestBody(r, &in)
	lwutil.CheckError(err, "err_decode_body")
	path := in

	if len(path) < 2 {
		lwutil.SendError("err_path_too_short", "")
	}

	for i, v := range path {
		if i > 0 {
			dist := math.Abs(float64(v[0]-path[i-1][0])) + math.Abs(float64(v[1]-path[i-1][1]))
			if dist > 3.1 || dist < 2.9 {
				lwutil.SendError("err_dist_not_3", fmt.Sprintf("dist=%f", dist))
			}
		}
	}

	//*get player info
	row := whDB.QueryRow("SELECT zoneCache, ap, maxAp, lastApTime, UTC_TIMESTAMP(), items, money, maxCardNum, pvpScore, pvpWinStreak FROM playerInfos WHERE userId=?", session.UserId)
	var zoneCacheStr []byte
	var ap uint32
	var maxAp uint32
	var lastApTimeStr string
	var nowStr string
	var itemsStr []byte
	var money uint32
	var maxCardNum uint32
	var pvpScore uint32
	var pvpWinStreak uint32
	err = row.Scan(&zoneCacheStr, &ap, &maxAp, &lastApTimeStr, &nowStr, &itemsStr, &money, &maxCardNum, &pvpScore, &pvpWinStreak)
	lwutil.CheckError(err, "")

	if len(zoneCacheStr) == 0 {
		lwutil.SendError("err_not_in_zone", "")
	}
	var cache zoneCache
	json.Unmarshal(zoneCacheStr, &cache)

	if len(lastApTimeStr) == 0 {
		lastApTimeStr = nowStr
	}
	lastApTime, err := time.ParseInLocation("2006-01-02 15:04:05", lastApTimeStr, time.UTC)
	lwutil.CheckError(err, "")
	now, err := time.ParseInLocation("2006-01-02 15:04:05", nowStr, time.UTC)
	lwutil.CheckError(err, "")

	var items map[string]uint32
	json.Unmarshal(itemsStr, &items)

	//*check path
	if cache.CurrPos != path[0] {
		lwutil.SendError("err_begin_coord", fmt.Sprintf("currPos=%v, path=%v", cache.CurrPos, path))
	}

	//*update ap
	if lastApTime.Unix() > now.Unix() {
		lastApTime = now
	}
	dSec := uint32(now.Unix() - lastApTime.Unix())

	dap := dSec / AP_ADD_DURATION
	if dap > 0 {
		ap = uint32(lwutil.Min(int64(maxAp), int64(ap+dap)))
	}
	if ap == maxAp {
		lastApTime = now
	} else {
		t := dSec % AP_ADD_DURATION
		lastApTime = time.Unix(now.Unix()-int64(t), 0)
	}

	apAddRemain := AP_ADD_DURATION - (dSec % AP_ADD_DURATION)

	if ap == 0 {
		lwutil.SendError("err_no_ap", "")
	}

	stepNum := len(path) - 1
	if stepNum > int(ap) {
		path = path[0:ap]
	}

	ap -= uint32(stepNum)

	//*update curr pos
	currPos := path[len(path)-1]
	cache.CurrPos = currPos

	//*prepare info collector
	monGrpId := uint32(0)
	hasPvp := false

	itemsAdd := make([]ItemInfo, 0, 8)
	cardsAdd := make([]uint32, 0, 8)
	moneyAdd := uint32(0)

	addItem := func(id uint32, num uint32) {
		itemsAdd = append(itemsAdd, ItemInfo{id, num})
	}
	addCard := func(id uint32) {
		cardsAdd = append(cardsAdd, id)
	}

	//*tile object
	posKey := fmt.Sprintf("%d,%d", currPos[0], currPos[1])
	objId, exist := cache.Objs[posKey]
	if exist {
		switch {
		case objId < 0: //battle
			monGrpId = uint32(-objId)
		case objId == 1: //wood case
			//fixme
		case objId == 2: //red case
			addItem(ITEM_ID_RED_CASE, 1)
		case objId == 3: //gold case
			addItem(ITEM_ID_GOLD_CASE, 1)
		case objId == 4: //small money bag
			addItem(ITEM_ID_MONEY_BAG_SMALL, 1)
		case objId == 5: //small money bag
			addItem(ITEM_ID_MONEY_BAG_BIG, 1)
		case objId == 6: //pvp
			hasPvp = true
		}
	}

	//*event
	eventId, exist := cache.Events[posKey]
	if exist {
		eventRow, ok := tblEvent[strconv.Itoa(int(eventId))]
		if ok {
			if eventRow.MonsterID != 0 {
				monGrpId = eventRow.MonsterID
			} else {
				if eventRow.Item1ID != 0 {
					addItem(eventRow.Item1ID, 1)
				}
				if eventRow.Item2ID != 0 {
					addItem(eventRow.Item2ID, 1)
				}
				if eventRow.Item3ID != 0 {
					addItem(eventRow.Item3ID, 1)
				}

				if eventRow.Card1ID != 0 {
					addCard(eventRow.Card1ID)
				}
				if eventRow.Card2ID != 0 {
					addCard(eventRow.Card2ID)
				}
				if eventRow.Card3ID != 0 {
					addCard(eventRow.Card3ID)
				}
			}
		} else {
			glog.Errorf("event not found in tblEvent: eventId=%d", eventId)
		}
	}

	//add items
	dMoney, redCase, goldCase := addItems(items, itemsAdd)
	moneyAdd += dMoney
	cache.RedCase += redCase
	cache.GoldCase += goldCase

	//*add money
	if moneyAdd > 0 {
		money += moneyAdd
	}

	//*add cards
	cards := make([]cardEntity, 0, 4)
	if len(cardsAdd) > 0 {
		protoAndLvs := make([]cardProtoAndLevel, len(cardsAdd))
		for i, card := range cardsAdd {
			protoAndLvs[i] = cardProtoAndLevel{card, 1}
		}
		cards, err = createCards(session.UserId, protoAndLvs, maxCardNum, WAGON_INDEX_TEMP, STR_MAP_EVENT_REWARD)
		lwutil.CheckError(err, "")
	}

	//*save battle or delete obj
	if monGrpId != 0 {
		cache.MonGrpId = monGrpId
	} else if objId != 0 {
		delete(cache.Objs, posKey)
	}

	//*pvp

	//*update db
	cacheJs, err := json.Marshal(cache)
	lwutil.CheckError(err, "")
	itemsJs, err := json.Marshal(items)
	lwutil.CheckError(err, "")

	_, err = whDB.Exec(`UPDATE playerInfos SET zoneCache=?, items=?, ap=?, lastApTime=?, money=? WHERE userid=?`,
		cacheJs, itemsJs, ap, lastApTime, money, session.UserId)
	lwutil.CheckError(err, "")

	//*out
	out := map[string]interface{}{
		"error":       nil,
		"in":          in,
		"zoneCache":   cache,
		"lastApTime":  lastApTime,
		"now":         now,
		"items":       items,
		"apAddRemain": apAddRemain,
		"monGrpId":    monGrpId,
		"hasPvp":      hasPvp,
		"cards":       cards,
		"cacheJs":     cacheJs,
		"itemsJs":     itemsJs,
	}
	lwutil.WriteResponse(w, out)
}

func regZone() {
	http.Handle("/whapi/zone/move", lwutil.ReqHandler(zoneMove))
}
