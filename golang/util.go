package main

import (
	"database/sql"
	"fmt"
	"github.com/garyburd/redigo/redis"
	_ "github.com/go-sql-driver/mysql"
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

	authDB = opendb("auth_db")
	authDB.SetMaxIdleConns(10)

	whDB = opendb("wh_db")
	whDB.SetMaxIdleConns(10)

	testDB = opendb("test")
	testDB.SetMaxIdleConns(10)
}

func opendb(dbname string) *sql.DB {
	db, err := sql.Open("mysql", fmt.Sprintf("root@/%s?parseTime=true", dbname))
	if err != nil {
		panic(err)
	}
	return db
}
