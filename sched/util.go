package main

import (
	"github.com/garyburd/redigo/redis"
	"strconv"
	"time"
	"encoding/csv"
	"os"
	"fmt"
	"reflect"
	"strings"
	"errors"
)

var redisPool *redis.Pool

func init() {
	redisPool = &redis.Pool{
		MaxIdle: 5,
		IdleTimeout: 240 * time.Second,
		Dial: func () (redis.Conn, error) {
			c, err := redis.Dial("tcp", "localhost:6379")
			if err != nil {
				return nil, err
			}
			return c, err
		},
	}

	err := test()
	fmt.Println(err)
}

func atoi(str string) int {
	i, err := strconv.Atoi(str)
	if err != nil {
		panic(err)
	}
	return i
}

func checkError(err error) {
	if err != nil {
		panic(err)
	}
}

func loadCsvTbl(file string, tbl interface{}, keycol string) error {
	f, err := os.Open(file)
	checkError(err)
	defer f.Close()

	//
	v := reflect.ValueOf(tbl).Elem()
	t := v.Type()
	if v.IsNil() {
		v.Set(reflect.MakeMap(t))
	}
	rowObjType := t.Elem()

	//
	reader := csv.NewReader(f)
	firstrow, err := reader.Read()
	keycolidx := -1
	for i, v := range firstrow {
		if strings.EqualFold(v, keycol) {
			keycolidx = i
			break
		}
	}
	if keycolidx == -1 {
		panic(fmt.Sprintf("keycol not find: %s", keycol))
	}

	row, err := reader.Read()
	for row != nil {
		rowobjValue := reflect.New(rowObjType).Elem()
		for i := 0; i < rowobjValue.NumField(); i++ {
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
					checkError(err)
					f.SetInt(n)
				case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
					n, err := strconv.ParseUint(valstr, 0, 64)
					checkError(err)
					f.SetUint(n)
				case reflect.Float32, reflect.Float64:
					n, err := strconv.ParseFloat(valstr, 64)
					checkError(err)
					f.SetFloat(n)
				case reflect.Bool:
					n, err := strconv.ParseBool(valstr)
					checkError(err)
					f.SetBool(n)
				case reflect.String:
					f.SetString(valstr)
				}
			}
		}

		v.SetMapIndex(reflect.ValueOf(row[keycolidx]), rowobjValue)

		row, err = reader.Read()
	}

	return nil
}