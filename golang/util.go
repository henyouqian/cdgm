package main

import (
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"github.com/garyburd/redigo/redis"
	_ "github.com/go-sql-driver/mysql"
	"github.com/golang/glog"
	"github.com/nu7hatch/gouuid"
	"net/http"
	"runtime"
	"time"
)

var redisPool *redis.Pool
var authDB *sql.DB
var matchDB *sql.DB
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

	matchDB = opendb("match_db")
	matchDB.SetMaxIdleConns(10)

	testDB = opendb("test")
	testDB.SetMaxIdleConns(10)
}

type Err struct {
	Error       string
	ErrorString string
}

func handleError(w http.ResponseWriter) {
	if r := recover(); r != nil {
		w.WriteHeader(http.StatusBadRequest)
		encoder := json.NewEncoder(w)

		var err Err
		switch r.(type) {
		case Err:
			err = r.(Err)
		default:
			err = Err{"err_internal", fmt.Sprintf("%v", r)}

			// buf := make([]byte, 1024)
			// runtime.Stack(buf, false)
			// glog.Errorf("%v\n%s\n", r, buf)
		}

		buf := make([]byte, 1024)
		runtime.Stack(buf, false)
		glog.Errorf("%v\n%s\n", r, buf)

		encoder.Encode(&err)
	}
}

func sendError(errType, errStr string) {
	panic(Err{errType, errStr})
}

func checkMathod(r *http.Request, method string) {
	if r.Method != method {
		sendError("err_method_not_allowed", "")
	}
}

func checkError(err error, errType string) {
	if err != nil {
		if errType == "" {
			errType = "err_internal"
		}
		sendError(errType, fmt.Sprintf("%v", err))
	}
}

func decodeRequestBody(r *http.Request, v interface{}) {
	decoder := json.NewDecoder(r.Body)
	err := decoder.Decode(v)
	checkError(err, "err_decode_body")
}

func writeResponse(w http.ResponseWriter, v interface{}) {
	encoder := json.NewEncoder(w)
	encoder.Encode(v)
}

func opendb(dbname string) *sql.DB {
	db, err := sql.Open("mysql", fmt.Sprintf("root@/%s?parseTime=true", dbname))
	checkError(err, "")
	return db
}

func sha224(s string) string {
	hasher := sha256.New224()
	hasher.Write([]byte(s))
	return base64.URLEncoding.EncodeToString(hasher.Sum(nil))
}

func checkAdmin(session *Session) {
	if session.Username != "admin" {
		sendError("err_denied", "")
	}
}

func genUUID() string {
	uuid, err := uuid.NewV4()
	checkError(err, "")
	return base64.URLEncoding.EncodeToString(uuid[:])
}

func repeatSingletonTask(key string, interval time.Duration, f func()) {
	rc := redisPool.Get()
	defer rc.Close()

	intervalMin := 10 * time.Millisecond
	if interval < intervalMin {
		interval = intervalMin
	}

	fingerprint := genUUID()
	redisKey := fmt.Sprintf("locker/%s", key)
	for {
		rdsfp, _ := redis.String(rc.Do("get", redisKey))
		if rdsfp == fingerprint {
			// it's mine
			_, err := rc.Do("expire", redisKey, int64(interval.Seconds())+1)
			checkError(err, "")
			f()
			time.Sleep(interval)
			continue
		} else {
			// takeup
			if rdsfp == "" {
				_, err := rc.Do("setex", redisKey, int64(interval.Seconds())+1, fingerprint)
				checkError(err, "")
				f()
				time.Sleep(interval)
				continue
			}
		}

		time.Sleep(1 * time.Second)
	}
}
