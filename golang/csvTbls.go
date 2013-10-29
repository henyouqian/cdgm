package main

import (
	"encoding/json"
	//"fmt"
	//"github.com/golang/glog"
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
	Display   bool
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
	Id         uint32
	ItemId     uint32
	Price      uint32
	Num        uint32
	Name       string
	Comment    string
	ItemIconID uint32
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
	ItemProb               float32
	MonsterProb            float32
	EventProb              float32
	PvpProb                float32
	OnlyItemProb           float32
	OnlyMonsterProb        float32
	WoodProb               float32
	TreasureProb           float32
	ChestProb              float32
	LittleGoldProb         float32
	BigGoldProb            float32
	Monster1ID             uint32
	Monster2ID             uint32
	Monster3ID             uint32
	Monster4ID             uint32
	Monster5ID             uint32
	Monster6ID             uint32
	Monster7ID             uint32
	Monster8ID             uint32
	Monster9ID             uint32
	Monster10ID            uint32
	EnterzonerdialogueID   uint32
	CompletezonedialogueID uint32
	BgmID                  uint32
	ResourceId             uint32
	BattleBgId             string
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

type rowLoginReward struct {
	Id            uint32
	LoginNum      uint32
	RewardCardsID uint32
}

type rowTask struct {
	Id      uint32
	Name    string
	Type    uint32
	Target  uint32
	Detail  uint32
	Content string
	Comment string
	Reward1 int32
	Amount1 uint32
	Reward2 int32
	Amount2 uint32
	Reward3 int32
	Amount3 uint32
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
	arrayLoginReward    []rowLoginReward
	tblTask             map[string]rowTask
)

func init() {
	err := lwutil.LoadCsvMap("../data/cards.csv", []string{"ID"}, &tblCard)
	lwutil.PanicIfError(err)
	err = lwutil.LoadCsvMap("../data/cardGrowthMappings.csv", []string{"type", "level"}, &tblCardGrowth)
	lwutil.PanicIfError(err)
	err = lwutil.LoadCsvMap("../data/cardLevels.csv", []string{"level"}, &tblCardLevel)
	lwutil.PanicIfError(err)
	err = lwutil.LoadCsvMap("../data/levels.csv", []string{"level"}, &tblWarlordCardLevel)
	lwutil.PanicIfError(err)

	//store
	err = lwutil.LoadCsvMap("../data/shops.csv", []string{"id"}, &tblStore)
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
			v.ItemIconID,
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
	err = lwutil.LoadCsvMap("../data/news.csv", []string{"id"}, &tblNews)
	lwutil.PanicIfError(err)

	// news list
	err = lwutil.LoadCsvArray("../data/news.csv", &tblNewsList)
	lwutil.PanicIfError(err)

	//instance
	err = lwutil.LoadCsvMap("../data/instance.csv", []string{"id"}, &tblInstance)
	lwutil.PanicIfError(err)

	// instance list
	err = lwutil.LoadCsvArray("../data/instance.csv", &tblInstanceList)
	lwutil.PanicIfError(err)

	//instance zone
	err = lwutil.LoadCsvMap("../data/instanceZones.csv", []string{"zoneId"}, &tblInstanceZone)
	lwutil.PanicIfError(err)

	// instance zone list
	err = lwutil.LoadCsvArray("../data/instanceZones.csv", &tblInstanceZoneList)
	lwutil.PanicIfError(err)

	//map
	err = lwutil.LoadCsvMap("../data/maps.csv", []string{"zoneID"}, &tblMap)
	lwutil.PanicIfError(err)

	//event
	err = lwutil.LoadCsvMap("../data/events.csv", []string{"ID"}, &tblEvent)
	lwutil.PanicIfError(err)

	//mapEvent
	err = lwutil.LoadCsvMap("../data/mapevents.csv", []string{"mapid", "tilevalue"}, &tblMapEvent)
	lwutil.PanicIfError(err)

	//LoginReward
	err = lwutil.LoadCsvArray("../data/loginRewards.csv", &arrayLoginReward)
	lwutil.PanicIfError(err)

	//task
	err = lwutil.LoadCsvMap("../data/task.csv", []string{"id"}, &tblTask)
	lwutil.PanicIfError(err)
}
