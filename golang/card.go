package main

import ()

type cardProtoAndLevel struct {
	proto uint32
	level uint32
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

func calcCardAttr(protoId uint32, level uint16) {

}

func createCards(ownerId uint32, protoAndLvs []cardProtoAndLevel) {

}
