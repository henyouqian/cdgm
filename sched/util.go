package main

import (
	"github.com/garyburd/redigo/redis"
	"strconv"
	"time"
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