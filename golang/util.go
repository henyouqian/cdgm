package main

import (
	//"database/sql"
	//"fmt"
	"github.com/garyburd/redigo/redis"
	_ "github.com/go-sql-driver/mysql"
	//"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"math/rand"
	"time"
)

var (
	redisPool *redis.Pool
	accountDB *lwutil.DB
	whDB      *lwutil.DB
	testDB    *lwutil.DB
	kvDB      *lwutil.DB
)

func init() {
	redisPool = &redis.Pool{
		MaxIdle:     20,
		MaxActive:   0,
		IdleTimeout: 240 * time.Second,
		Dial: func() (redis.Conn, error) {
			c, err := redis.Dial("tcp", "localhost:6379")
			if err != nil {
				return nil, err
			}
			return c, err
		},
	}

	var err error
	accountDB, err = lwutil.OpenDb("account_db")
	lwutil.CheckError(err, "")
	accountDB.SetMaxIdleConns(10)

	whDB, err = lwutil.OpenDb("wh_db")
	lwutil.CheckError(err, "")
	whDB.SetMaxIdleConns(10)

	testDB, err = lwutil.OpenDb("test")
	lwutil.CheckError(err, "")
	testDB.SetMaxIdleConns(2)

	kvDB, err = lwutil.OpenDb("kv_db")
	lwutil.CheckError(err, "")
	kvDB.SetMaxIdleConns(10)

	lwutil.StartKV(kvDB, redisPool)
}

type WeightedRandom struct {
	uppers []float32
}

func newWeightedRandom(totalWeight float32, weights ...float32) *WeightedRandom {
	var w WeightedRandom
	sum := float32(0)
	for _, weight := range weights {
		sum += weight
		w.uppers = append(w.uppers, sum)
	}

	if totalWeight > 0 {
		sum = totalWeight
	}

	for i, v := range w.uppers {
		w.uppers[i] = v / sum
	}

	return &w
}

func (w *WeightedRandom) get() int32 {
	rdm := rand.Float32()
	idx := int32(0)
	for _, upper := range w.uppers {
		if rdm <= upper {
			return idx
		}
		idx++
	}
	return -1
}
