package main

import (
	"database/sql"
	"github.com/garyburd/redigo/redis"
	_ "github.com/go-sql-driver/mysql"
	"github.com/henyouqian/golangUtil"
	"time"
)

var redisPool *redis.Pool
var authDB *sql.DB
var whDB *sql.DB
var testDB *sql.DB

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

	authDB = lwutil.Opendb("auth_db")
	authDB.SetMaxIdleConns(10)

	whDB = lwutil.Opendb("wh_db")
	whDB.SetMaxIdleConns(10)

	testDB = lwutil.Opendb("test")
	testDB.SetMaxIdleConns(10)
}
