package main

import (
	"encoding/csv"
	"errors"
	"fmt"
	"github.com/henyouqian/golangUtil"
	"os"
	"reflect"
	"strconv"
	"strings"
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
	err := loadCsvTbl("../data/cards.csv", []string{"ID"}, &tblCard)
	lwutil.AssertNoError(err)
	err = loadCsvTbl("../data/cardGrowthMappings.csv", []string{"type", "level"}, &tblCardGrowth)
	lwutil.AssertNoError(err)
	err = loadCsvTbl("../data/cardLevels.csv", []string{"level"}, &tblCardLevel)
	lwutil.AssertNoError(err)
	err = loadCsvTbl("../data/levels.csv", []string{"level"}, &tblWarlordCardLevel)
	lwutil.AssertNoError(err)
}

func loadCsvTbl(file string, keycols []string, tbl interface{}) (e error) {
	f, err := os.Open(file)
	if err != nil {
		return err
	}
	defer f.Close()

	//
	v := reflect.ValueOf(tbl).Elem()
	defer func() {
		if r := recover(); r != nil {
			e = errors.New(fmt.Sprintf("tbl's type must be map[string]struct. detail:%v", r))
		}
	}()

	t := v.Type()
	if v.IsNil() {
		v.Set(reflect.MakeMap(t))
	}
	rowObjType := t.Elem()

	//
	reader := csv.NewReader(f)
	firstrow, err := reader.Read()
	keycolidxs := make([]int, len(keycols))
	for icol, vcol := range keycols {
		found := false
		for i, v := range firstrow {
			if strings.EqualFold(v, vcol) {
				keycolidxs[icol] = i
				found = true
				break
			}
		}
		if !found {
			return errors.New(fmt.Sprintf("column not found: %s in %s", vcol, file))
		}
	}

	if len(keycolidxs) != len(keycols) {
		errors.New(fmt.Sprintf("keys not match totally: keycols = %v", keycols))
	}

	row, err := reader.Read()
	for row != nil {
		rowobjValue := reflect.New(rowObjType).Elem()
		numField := rowobjValue.NumField()
		for i := 0; i < numField; i++ {
			f := rowobjValue.Field(i)
			colname := rowobjValue.Type().Field(i).Name

			colidx := -1
			for i, v := range firstrow {
				if strings.EqualFold(colname, v) {
					colidx = i
					break
				}
			}
			if colidx != -1 {
				valstr := row[colidx]
				switch f.Kind() {
				case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
					n, err := strconv.ParseInt(valstr, 0, 64)
					if err != nil {
						return err
					}
					f.SetInt(n)
				case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
					n, err := strconv.ParseUint(valstr, 0, 64)
					if err != nil {
						return err
					}
					f.SetUint(n)
				case reflect.Float32, reflect.Float64:
					n, err := strconv.ParseFloat(valstr, 64)
					if err != nil {
						return err
					}
					f.SetFloat(n)
				case reflect.Bool:
					n, err := strconv.ParseBool(valstr)
					if err != nil {
						return err
					}
					f.SetBool(n)
				case reflect.String:
					f.SetString(valstr)
				}
			}
		}

		keys := make([]string, len(keycolidxs))
		for i, v := range keycolidxs {
			keys[i] = row[v]
		}
		v.SetMapIndex(reflect.ValueOf(strings.Join(keys, ",")), rowobjValue)

		row, err = reader.Read()
	}

	return nil
}
