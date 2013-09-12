package main

import (
	"errors"
	"fmt"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwUtil"
	"strconv"
)

type cardProtoAndLevel struct {
	proto uint32
	level uint16
}

type cardEntity struct {
	Id          uint64
	ProtoId     uint32
	OwnerId     uint32
	InPackage   bool
	Level       uint16
	Exp         uint32
	Skill1Id    uint16
	Skill1Level uint8
	Skill1Exp   uint16
	Skill2Id    uint16
	Skill2Level uint8
	Skill2Exp   uint16
	Skill3Id    uint16
	Skill3Level uint8
	Skill3Exp   uint16
	Hp          uint16
	Atk         uint16
	Def         uint16
	Wis         uint16
	Agi         uint16
	HpCrystal   uint16
	AtkCrystal  uint16
	DefCrystal  uint16
	WisCrystal  uint16
	AgiCrystal  uint16
	HpExtra     uint16
	AtkExtra    uint16
	DefExtra    uint16
	WisExtra    uint16
	AgiExtra    uint16
}

type cardAttr struct {
	Hp  uint16
	Atk uint16
	Def uint16
	Wis uint16
	Agi uint16
}

func isWarlord(protoId uint32) bool {
	return protoId <= WARLORD_MAX && protoId >= WARLORD_MIN
}

func calcCardAttr(protoId uint32, level uint16) (*cardAttr, error) {
	cardProto, ok := tblCard[strconv.FormatUint(uint64(protoId), 10)]
	if !ok {
		return nil, errors.New(fmt.Sprintf("car not found: protoId=%d", protoId))
	}

	maxLevel := cardProto.MaxLevel
	if level > maxLevel {
		return nil, errors.New(fmt.Sprint("level > cardProto: level=%d, maxLevle=%d", level, cardProto.MaxLevel))
	}

	//
	growType := cardProto.GrowType
	growMin := tblCardGrowth[fmt.Sprintf("%d,1", growType)].Curve
	growMax := tblCardGrowth[fmt.Sprintf("%d,%d", growType, maxLevel)].Curve
	growCurr := tblCardGrowth[fmt.Sprintf("%d,%d", growType, level)].Curve

	//
	var f float32
	if growMin != growMax {
		f = float32(growCurr-growMin) / float32(growMax-growMin)
	}

	//
	lerp := func(min, max, f float32) uint16 {
		return uint16(min + (max-min)*f)
	}
	hp := lerp(float32(cardProto.BaseHp), float32(cardProto.MaxHp), f)
	atk := lerp(float32(cardProto.BaseAtk), float32(cardProto.MaxAtk), f)
	def := lerp(float32(cardProto.BaseDef), float32(cardProto.MaxDef), f)
	wis := lerp(float32(cardProto.BaseWis), float32(cardProto.MaxWis), f)
	agi := lerp(float32(cardProto.BaseAgi), float32(cardProto.MaxAgi), f)

	cardAttr := cardAttr{hp, atk, def, wis, agi}
	return &cardAttr, nil
}

func createCards(ownerId uint32, protoAndLvs []cardProtoAndLevel, maxCardNum uint16) error {
	cards := make([]cardEntity, len(protoAndLvs))
	for i, v := range protoAndLvs {
		attr, err := calcCardAttr(v.proto, v.level)
		if err != nil {
			return err
		}

		//
		cardProto, ok := tblCard[strconv.FormatUint(uint64(v.proto), 10)]
		if !ok {
			return errors.New(fmt.Sprintf("car not found: protoId=%d", v.proto))
		}

		//
		lvExpTbl := &tblCardLevel
		if isWarlord(v.proto) {
			lvExpTbl = &tblWarlordCardLevel
		}
		row, ok := (*lvExpTbl)[strconv.FormatUint(uint64(v.level), 10)]
		if !ok {
			return errors.New(fmt.Sprintf("invalid level: %d", v.level))
		}
		exp := row.Exp

		//
		card := cardEntity{
			ProtoId:     v.proto,
			OwnerId:     ownerId,
			Level:       v.level,
			Exp:         exp,
			Hp:          attr.Hp,
			Atk:         attr.Atk,
			Def:         attr.Def,
			Wis:         attr.Wis,
			Agi:         attr.Agi,
			HpCrystal:   0,
			AtkCrystal:  0,
			DefCrystal:  0,
			WisCrystal:  0,
			AgiCrystal:  0,
			HpExtra:     0,
			AtkExtra:    0,
			DefExtra:    0,
			WisExtra:    0,
			AgiExtra:    0,
			Skill1Id:    cardProto.SkillId1,
			Skill1Level: 1,
			Skill1Exp:   0,
			Skill2Id:    cardProto.SkillId2,
			Skill2Level: 1,
			Skill2Exp:   0,
			Skill3Id:    0,
			Skill3Level: 1,
			Skill3Exp:   0,
		}

		cards[i] = card
	}

	//get card num in package
	row := whDB.QueryRow("SELECT COUNT(1) FROM cardEntities WHERE ownerId=? AND inPackage=1", ownerId)
	var inpackNum uint16
	err := row.Scan(&inpackNum)
	if err != nil {
		return err
	}

	//
	gotoPackNum := lwutil.Min(int64(maxCardNum-inpackNum), int64(len(cards)))

	// insert transaction
	func() error {
		//tx, err := whDB.Begin()
		//if err != nil {
		//	return err
		//}
		//defer lwutil.EndTx(tx, &err)

		//stmt, err := tx.Prepare("INSERT INTO cardEntities (a, b, c, d) VALUES (?, ?, ?, ?)")
		//if err != nil {
		//	return err
		//}

		//ids := make([]int64, insertCount)
		//for i := 0; i < insertCount; i++ {
		//	res, err := stmt.Exec(1, 2, 3, 4)
		//	lwutil.CheckError(err, "err_account_exists")

		//	ids[i], err = res.LastInsertId()
		//	lwutil.CheckError(err, "")
		//}
		return nil
	}()

	_ = gotoPackNum

	return nil
}
