package main

import (
	"encoding/json"
	//"fmt"
	"github.com/henyouqian/lwutil"
)

type rowCard struct {
	Id        uint32
	Name      string
	Rarity    uint8
	CardType  uint8
	BattleExp uint32
	Price     uint32
	BaseHp    uint16
	BaseAtk   uint16
	BaseDef   uint16
	BaseWis   uint16
	BaseAgi   uint16
	MaxHp     uint16
	MaxAtk    uint16
	MaxDef    uint16
	MaxWis    uint16
	MaxAgi    uint16
	MaxLevel  uint16
	GrowType  uint8
	SkillId1  uint16
	SkillId2  uint16
}

type rowCardGrowth struct {
	Type  uint8
	Level uint16
	Curve uint16
}

type rowCardLevel struct {
	Level uint16
	Exp   uint32
}

type rowStore struct {
	Id      uint32
	ItemId  uint32
	Price   uint32
	Num     uint32
	Name    string
	Comment string
	IconId  uint32
}

type rowNews struct {
	Id          uint32
	Date        string
	Title       string
	NewsContent string
	PicUrl      string
}

type rowInstance struct {
	Id            uint32
	Name          string
	Type          uint32
	LevelRestrict uint32
	ZoneRestrict  uint32
	TimesRestrict uint32
	DisplayOrder  uint32
	OpenDate      string
	CloseDate     string
	CoolDown      uint32
}

type rowInstanceZone struct {
	ZoneId        uint32
	InstanceID    uint32
	ResourceId    uint32
	Name          string
	Comment       string
	Difficulty    uint32
	LevelRestrict uint32
	XpCost        uint32
	ZoneNo        uint32
	NextZoneId    uint32
	Price         uint32
	BgmId         uint32
	DropCard1Id   uint32
	DropCard2Id   uint32
	DropCard3Id   uint32
	DropCard4Id   uint32
	DropCard5Id   uint32
	DropCard6Id   uint32
	DropItem1Id   uint32
	DropItem2Id   uint32
	DropItem3Id   uint32
	DropItem4Id   uint32
	DropItem5Id   uint32
	DropItem6Id   uint32
}

type rowMap struct {
	ItemProb       float32 `json:"item%"`
	MonsterProb    float32 `json:"monster%"`
	EventProb      float32 `json:"event%"`
	PvpProb        float32 `json:"PVP%"`
	WoodProb       float32 `json:"wood%"`
	RedCaseProb    float32 `json:"treasure%"`
	GoldCaseProb   float32 `json:"chest%"`
	LittleGoldProb float32 `json:"littlegold%"`
	BigGoldProb    float32 `json:"biggold%"`
	Monster1ID     uint32  `json:"monster1ID"`
	Monster2ID     uint32  `json:"monster2ID"`
	Monster3ID     uint32  `json:"monster3ID"`
	Monster4ID     uint32  `json:"monster4ID"`
	Monster5ID     uint32  `json:"monster5ID"`
	Monster6ID     uint32  `json:"monster6ID"`
	Monster7ID     uint32  `json:"monster7ID"`
	Monster8ID     uint32  `json:"monster8ID"`
	Monster9ID     uint32  `json:"monster9ID"`
	Monster10ID    uint32  `json:"monster10ID"`
	EnterDialog    uint32  `json:"enterzonerdialogueID"`
	CompleteDialog uint32  `json:"completezonedialogueID"`
}

type rowEvent struct {
	Id              uint32
	EventType       uint32
	Repeat          uint32
	StartdialogueID uint32
	OverdialogueID  uint32
	MonsterID       uint32
	Item1ID         uint32
	Amount1         uint32
	Item2ID         uint32
	Amount2         uint32
	Item3ID         uint32
	Amount3         uint32
	Card1ID         uint32
	Card2ID         uint32
	Card3ID         uint32
}

type rowMapEvent struct {
	MapId     uint32
	TileValue uint32
	EventId   uint32
}

var (
	tblCard             map[string]rowCard
	tblCardGrowth       map[string]rowCardGrowth
	tblCardLevel        map[string]rowCardLevel
	tblWarlordCardLevel map[string]rowCardLevel
	tblStore            map[string]rowStore
	goodsReply          []byte
	tblNews             map[string]rowNews
	tblNewsList         []rowNews
	tblInstance         map[string]rowInstance
	tblInstanceList     []rowInstance
	tblInstanceZone     map[string]rowInstanceZone
	tblInstanceZoneList []rowInstanceZone
	tblMap              map[string]rowMap
	tblEvent            map[string]rowEvent
	tblMapEvent         map[string]rowMapEvent
)

func init() {
	err := lwutil.LoadCsvTbl("../data/cards.csv", []string{"ID"}, &tblCard)
	lwutil.PanicIfError(err)
	err = lwutil.LoadCsvTbl("../data/cardGrowthMappings.csv", []string{"type", "level"}, &tblCardGrowth)
	lwutil.PanicIfError(err)
	err = lwutil.LoadCsvTbl("../data/cardLevels.csv", []string{"level"}, &tblCardLevel)
	lwutil.PanicIfError(err)
	err = lwutil.LoadCsvTbl("../data/levels.csv", []string{"level"}, &tblWarlordCardLevel)
	lwutil.PanicIfError(err)

	//store
	err = lwutil.LoadCsvTbl("../data/shops.csv", []string{"id"}, &tblStore)
	lwutil.PanicIfError(err)

	var tblStoreList []rowStore
	err = lwutil.LoadCsvArray("../data/shops.csv", &tblStoreList)
	lwutil.PanicIfError(err)

	type Goods struct {
		GoodsId uint32 `json:"goodsId"`
		Price   uint32 `json:"price"`
		IconId  uint32 `json:"iconId"`
		ItemId  uint32 `json:"itemId"`
		Name    string `json:"name"`
		Comment string `json:"comment"`
	}

	goodsList := make([]Goods, 0, 8)
	for _, v := range tblStoreList {
		goods := Goods{
			v.Id,
			v.Price,
			v.IconId,
			v.ItemId,
			v.Name,
			v.Comment,
		}
		goodsList = append(goodsList, goods)
	}

	type GoodsReply struct {
		Goods []Goods `json:"goods"`
	}
	goodsRp := GoodsReply{goodsList}

	goodsReply, err = json.Marshal(&goodsRp)
	lwutil.PanicIfError(err)

	//news
	err = lwutil.LoadCsvTbl("../data/news.csv", []string{"id"}, &tblNews)
	lwutil.PanicIfError(err)

	// news list
	err = lwutil.LoadCsvArray("../data/news.csv", &tblNewsList)
	lwutil.PanicIfError(err)

	//instance
	err = lwutil.LoadCsvTbl("../data/instance.csv", []string{"id"}, &tblInstance)
	lwutil.PanicIfError(err)

	// instance list
	err = lwutil.LoadCsvArray("../data/instance.csv", &tblInstanceList)
	lwutil.PanicIfError(err)

	//instance zone
	err = lwutil.LoadCsvTbl("../data/instanceZones.csv", []string{"zoneId"}, &tblInstanceZone)
	lwutil.PanicIfError(err)

	// instance zone list
	err = lwutil.LoadCsvArray("../data/instanceZones.csv", &tblInstanceZoneList)
	lwutil.PanicIfError(err)

	//map
	err = lwutil.LoadCsvTbl("../data/maps.csv", []string{"zoneID"}, &tblMap)
	lwutil.PanicIfError(err)

	//event
	err = lwutil.LoadCsvTbl("../data/events.csv", []string{"ID"}, &tblEvent)
	lwutil.PanicIfError(err)

	//mapEvent
	err = lwutil.LoadCsvTbl("../data/mapevents.csv", []string{"mapid", "tilevalue"}, &tblMapEvent)
	lwutil.PanicIfError(err)

}
