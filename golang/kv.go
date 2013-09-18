package main

import (
	"database/sql"
	"github.com/garyburd/redigo/redis"
	//"time"
	"github.com/henyouqian/lwutil"
)

const ()

var (
	kvDB *sql.DB
)

func init() {
	kvDB = opendb("kv_db")
	kvDB.SetMaxIdleConns(10)
}

const (
	CACHE_LIFE_SEC = 3600
	SCRIPT_SET_KV  = `
		redis.call('set', 'kv/'..KEYS[1], KEYS[2])
		redis.call('zadd', 'kvz', KEYS[3], KEYS[1])
	`
)

func setKV(key string, value []byte) error {
	rc := redisPool.Get()
	defer rc.Close()

	expireTime := lwutil.GetRedisTime() + CACHE_LIFE_SEC

	_, err := rc.Do("eval", SCRIPT_SET_KV, 3, key, value, expireTime)
	if err != nil {
		return lwutil.NewErr(err)
	}
	return nil
}

func getKV(key string) ([]byte, error) {
	rc := redisPool.Get()
	defer rc.Close()

	v, err := rc.Do("get", "kv/"+key)
	if err != nil {
		err = lwutil.NewErr(err)
	}
	if v == nil {
		return nil, nil
	}
	s, err := redis.Bytes(v, err)
	return s, err
}
