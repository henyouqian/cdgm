package main

import (
	"database/sql"
	"flag"
	"fmt"
	"github.com/garyburd/redigo/redis"
	"github.com/golang/glog"
	"net/http"
	"runtime"
	"time"
)

var (
	redisPool *redis.Pool
	logDB     *sql.DB
)

func opendb(dbname string) *sql.DB {
	db, err := sql.Open("mysql", fmt.Sprintf("root@/%s?parseTime=true", dbname))
	if err != nil {
		panic(err)
	}
	return db
}

func initRedisAndDb() {
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

	logDB = opendb("whlog_db")
	logDB.SetMaxIdleConns(10)
}

func staticFile(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, r.URL.Path[1:])
}

func main() {
	var port int
	flag.IntVar(&port, "port", 8001, "server port")
	flag.Parse()

	regLog()

	http.HandleFunc("/static/", staticFile)

	runtime.GOMAXPROCS(runtime.NumCPU())

	glog.Infof("Server running: cpu=%d, port=%d", runtime.NumCPU(), port)
	glog.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}
