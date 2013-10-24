package main

import (
	"fmt"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"strconv"
	"strings"
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
		return nil, lwutil.NewErrStr(fmt.Sprintf("car not found: protoId=%d", protoId))
	}

	maxLevel := cardProto.MaxLevel
	if level > maxLevel {
		return nil, lwutil.NewErrStr(fmt.Sprint("level > cardProto: level=%d, maxLevle=%d", level, cardProto.MaxLevel))
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

func createCards(ownerId uint32, protoAndLvs []cardProtoAndLevel, maxCardNum uint16, wagonIdx uint8, desc string) ([]*cardEntity, error) {
	cardNum := len(protoAndLvs)
	if cardNum == 0 {
		return nil, lwutil.NewErrStr("protoAndLvs is empty")
	}
	cards := make([]*cardEntity, cardNum)
	cardProtos := make([]uint32, cardNum)
	for i, v := range protoAndLvs {
		attr, err := calcCardAttr(v.proto, v.level)
		if err != nil {
			return nil, err
		}

		//
		cardProto, ok := tblCard[strconv.FormatUint(uint64(v.proto), 10)]
		if !ok {
			return nil, lwutil.NewErrStr(fmt.Sprintf("car not found: protoId=%d", v.proto))
		}

		//
		lvExpTbl := &tblCardLevel
		if isWarlord(v.proto) {
			lvExpTbl = &tblWarlordCardLevel
		}
		row, ok := (*lvExpTbl)[strconv.FormatUint(uint64(v.level), 10)]
		if !ok {
			return nil, lwutil.NewErrStr(fmt.Sprintf("invalid level: %d", v.level))
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

		cards[i] = &card
		cardProtos[i] = v.proto
	}

	//get card num in package
	row := whDB.QueryRow("SELECT COUNT(1) FROM cardEntities WHERE ownerId=? AND inPackage=1", ownerId)
	var inpackNum uint16
	err := row.Scan(&inpackNum)
	if err != nil {
		return nil, err
	}

	//
	glog.Infoln(int64(maxCardNum-inpackNum), cardNum)
	gotoPackNum := lwutil.Truncate(int64(maxCardNum)-int64(inpackNum), 0, int64(cardNum))
	wcInfos := make([]wagonCardInfo, 0, 10)

	// insert transaction
	err = func() error {
		tx, err := whDB.Begin()
		if err != nil {
			return lwutil.NewErr(err)
		}
		defer lwutil.EndTx(tx, &err)

		fields, err := lwutil.GetStructFieldKeys(cards[0])
		if err != nil {
			return lwutil.NewErr(err)
		}
		fieldStr := strings.Join(fields, ",")
		ques := make([]string, len(fields))
		for i, _ := range ques {
			ques[i] = "?"
		}
		quesStr := strings.Join(ques, ",")
		stmt, err := tx.Prepare(fmt.Sprintf("INSERT INTO cardEntities (%s) VALUES (%s)", fieldStr, quesStr))
		if err != nil {
			lwutil.NewErr(err)
		}

		for i := 0; i < cardNum; i++ {
			card := cards[i]

			if i < int(gotoPackNum) {
				card.InPackage = true
			} else {
				card.InPackage = false
				wcInfo := wagonCardInfo{card.Id, card.ProtoId}
				wcInfos = append(wcInfos, wcInfo)
			}

			values, err := lwutil.GetStructFieldValues(card)
			if err != nil {
				return lwutil.NewErr(err)
			}

			res, err := stmt.Exec(values...)
			if err != nil {
				return lwutil.NewErr(err)
			}

			cardId, err := res.LastInsertId()
			if err != nil {
				return lwutil.NewErr(err)
			}
			card.Id = uint64(cardId)
		}
		return nil
	}()

	if err != nil {
		return nil, err
	}

	// add to wagon
	if len(wcInfos) != 0 {
		wagonAddCards(wagonIdx, ownerId, wcInfos, desc)
	}

	//
	addCardCollect(ownerId, cardProtos)

	return cards, nil
}

func addCardCollect(userId uint32, cardIds []uint32) error {
	rc := redisPool.Get()
	defer rc.Close()

	var collectedCards []uint32
	key := fmt.Sprintf("cardCollect/%d", userId)
	_, err := lwutil.GetKvDb(key, &collectedCards)
	if err != nil {
		return lwutil.NewErr(err)
	}

	cardMap := make(map[uint32]bool)
	for _, v := range collectedCards {
		cardMap[v] = true
	}

	for _, v := range cardIds {
		cardMap[v] = true
	}

	cardIds = make([]uint32, len(cardMap), 0)
	for k, _ := range cardMap {
		cardRow, ok := tblCard[strconv.Itoa(int(k))]
		if ok && cardRow.Display {
			cardIds = append(cardIds, k)
		}
	}

	err = lwutil.SetKvDb(key, &cardIds)
	if err != nil {
		return lwutil.NewErr(err)
	}
	return nil
}

func getCollection(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	rc := redisPool.Get()
	defer rc.Close()

	session, err := findSession(w, r, rc)
	lwutil.CheckError(err, "err_auth")

	//
	collectedCards := make([]uint32, 0)
	_, err = lwutil.GetKvDb(fmt.Sprintf("cardCollect/%d", session.UserId), &collectedCards)
	lwutil.CheckError(err, "")

	//out
	out := map[string]interface{}{
		"collection": collectedCards,
	}

	lwutil.WriteResponse(w, &out)
}

func regCard() {
	http.Handle("/whapi/card/collection", lwutil.ReqHandler(getCollection))
}
