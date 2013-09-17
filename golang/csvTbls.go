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

var (
	tblCard             map[string]rowCard
	tblCardGrowth       map[string]rowCardGrowth
	tblCardLevel        map[string]rowCardLevel
	tblWarlordCardLevel map[string]rowCardLevel
	tblStore            []rowStore
	goodsReply          []byte
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

	err = lwutil.LoadCsvArray("../data/shops.csv", &tblStore)
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
	for _, v := range tblStore {
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
	goodsReply, err = json.Marshal(&goodsList)
	lwutil.PanicIfError(err)
}
