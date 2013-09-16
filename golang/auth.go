package main

import (
	"fmt"
	//_ "github.com/go-sql-driver/mysql"
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"github.com/garyburd/redigo/redis"
	"github.com/henyouqian/lwutil"
	"net/http"
)

const sessionLifeSecond = 60 * 60 * 24 * 7

type Session struct {
	Userid   uint64
	Username string
	Appid    uint32
}

func newSession(w http.ResponseWriter, rc redis.Conn, userid uint64, username string, appid uint32) (usertoken string, err error) {
	tokenkey := fmt.Sprintf("%d/tokenkey", userid)
	usertokenRaw, err := rc.Do("get", tokenkey)
	if err != nil {
		return usertoken, lwutil.NewErr(err)
	}
	if usertokenRaw != nil {
		usertoken, err := redis.String(usertokenRaw, err)
		if err != nil {
			return usertoken, lwutil.NewErr(err)
		}
		rc.Do("del", fmt.Sprintf("%s", usertoken))
	}

	usertoken = lwutil.GenUUID()

	session := Session{userid, username, appid}
	jsonSession, err := json.Marshal(session)
	if err != nil {
		return usertoken, lwutil.NewErr(err)
	}

	rc.Send("setex", usertoken, sessionLifeSecond, jsonSession)
	rc.Send("setex", tokenkey, sessionLifeSecond, usertoken)
	if err = rc.Flush(); err != nil {
		return usertoken, lwutil.NewErr(err)
	}

	// cookie
	http.SetCookie(w, &http.Cookie{Name: "token", Value: usertoken, MaxAge: sessionLifeSecond, Path: "/"})

	return usertoken, err
}

func findSession(w http.ResponseWriter, r *http.Request) (*Session, error) {
	usertoken := r.FormValue("token")
	if usertoken == "" {
		usertokenCookie, err := r.Cookie("token")
		if err == nil {
			usertoken = usertokenCookie.Value
		} else {
			return nil, lwutil.NewErrStr("no token")
		}
	}

	//redis
	rc := redisPool.Get()
	defer rc.Close()

	sessionBytes, err := redis.Bytes(rc.Do("get", usertoken))
	if err != nil {
		return nil, err
	}

	var session Session
	if err = json.Unmarshal(sessionBytes, &session); err != nil {
		return nil, lwutil.NewErr(err)
	}

	return &session, nil
}

func login(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "POST")

	// input
	var input struct {
		Username  string
		Password  string
		Appsecret string
	}
	err := lwutil.DecodeRequestBody(r, &input)
	lwutil.CheckError(err, "err_decode_body")

	if input.Username == "" || input.Password == "" {
		lwutil.SendError("err_input", "")
	}

	sha1 := func(s string) string {
		hasher := sha1.New()
		hasher.Write([]byte(s))
		return hex.EncodeToString(hasher.Sum(nil))
	}

	pwsha := sha1(input.Password)

	// get userid
	row := accountDB.QueryRow("SELECT id FROM user_account WHERE username=? AND password=?", input.Username, pwsha)
	var userid uint64
	err = row.Scan(&userid)
	lwutil.CheckError(err, "err_not_match")

	// new session
	rc := redisPool.Get()
	defer rc.Close()

	appid := uint32(555)
	usertoken, err := newSession(w, rc, userid, input.Username, appid)
	lwutil.CheckError(err, "")

	// reply
	lwutil.WriteResponse(w, usertoken)
}

func regStore() {
	http.Handle("/authapi/login", lwutil.ReqHandler(login))
}
