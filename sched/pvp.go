package main

import (
	"fmt"
	"time"
	"github.com/garyburd/redigo/redis"
)


var pool *redis.Pool


func init() {
	pool = &redis.Pool{
		MaxIdle: 5,
		IdleTimeout: 240 * time.Second,
		Dial: func () (redis.Conn, error) {
			c, err := redis.Dial("tcp", "localhost:6379")
			if err != nil {
				return nil, err
			}
			// if err := c.Do("AUTH", password); err != nil {
			// 	c.Close()
			// 	return nil, err
			// }
			return c, err
		},
		TestOnBorrow: func(c redis.Conn, t time.Time) error {
			_, err := c.Do("PING")
			return err
		},
	}
	fmt.Println(pool)
}



func pvpMain(){
	for {
		fmt.Println("in pvp loop")

		conn := pool.Get()
		defer conn.Close()

		exists, err := redis.Bool(conn.Do("EXISTS", "bafdf"))
		if err != nil {
			// handle error return from c.Do or type conversion error.
		}

		fmt.Println(exists)


		time.Sleep(2000 * time.Millisecond)
	}
}
