package main

import (
	"github.com/henyouqian/lwUtil"
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

var (
	tblCard             map[string]rowCard
	tblCardGrowth       map[string]rowCardGrowth
	tblCardLevel        map[string]rowCardLevel
	tblWarlordCardLevel map[string]rowCardLevel
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
}
