package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/garyburd/redigo/redis"
	"github.com/henyouqian/golangUtil"
	"net/http"
	"time"
)

const passwordSalt = "liwei"
const sessionLifeSecond = 60 * 60 * 24 * 7
const sessionUpdateSecond = 60 * 60

type Session struct {
	Userid   uint64
	Username string
	Born     time.Time
	Appid    uint32
}

func newSession(w http.ResponseWriter, rc redis.Conn, userid uint64, username string, appid uint32) (usertoken string, err error) {
	usertoken = ""
	usertokenRaw, err := rc.Do("get", fmt.Sprintf("usertokens/%d+%d", userid, appid))
	lwutil.CheckError(err, "")
	if usertokenRaw != nil {
		usertoken, err := redis.String(usertokenRaw, err)
		if err != nil {
			return usertoken, err
		}
		rc.Do("del", fmt.Sprintf("sessions/%s", usertoken))
	}

	usertoken = lwutil.GenUUID()

	session := Session{userid, username, time.Now(), appid}
	jsonSession, err := json.Marshal(session)
	if err != nil {
		return usertoken, err
	}

	rc.Send("setex", fmt.Sprintf("sessions/%s", usertoken), sessionLifeSecond, jsonSession)
	rc.Send("setex", fmt.Sprintf("usertokens/%d+%d", userid, appid), sessionLifeSecond, usertoken)
	rc.Flush()
	for i := 0; i < 2; i++ {
		_, err = rc.Receive()
		lwutil.CheckError(err, "")
	}

	// cookie
	http.SetCookie(w, &http.Cookie{Name: "usertoken", Value: usertoken, MaxAge: sessionLifeSecond, Path: "/"})

	return usertoken, err
}

func findSession(w http.ResponseWriter, r *http.Request) (*Session, error) {
	session := new(Session)

	usertokenCookie, err := r.Cookie("usertoken")
	if err != nil {
		return session, errors.New("usertoken not in cookie")
	}
	usertoken := usertokenCookie.Value

	//redis
	rc := redisPool.Get()
	defer rc.Close()

	sessionBytes, err := redis.Bytes(rc.Do("get", fmt.Sprintf("sessions/%s", usertoken)))
	if err != nil {
		return session, err
	}

	err = json.Unmarshal(sessionBytes, &session)
	lwutil.CheckError(err, "")

	//update session
	dt := time.Now().Sub(session.Born)
	if dt > sessionUpdateSecond*time.Second {
		newSession(w, rc, session.Userid, session.Username, session.Appid)
	}

	return session, nil
}

func checkAdmin(session *Session) {
	if session.Username != "admin" {
		lwutil.SendError("err_denied", "")
	}
}

func register(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
	lwutil.CheckMathod(r, "POST")

	// input
	type Input struct {
		Username string
		Password string
	}
	var input Input
	lwutil.DecodeRequestBody(r, &input)

	if input.Username == "" || input.Password == "" {
		lwutil.SendError("err_input", "")
	}

	pwsha := lwutil.Sha224(input.Password + passwordSalt)

	// insert into db
	stmt, err := authDB.Prepare("INSERT INTO user_accounts (username, password) VALUES (?, ?)")
	lwutil.CheckError(err, "")

	res, err := stmt.Exec(input.Username, pwsha)
	lwutil.CheckError(err, "err_account_exists")

	id, err := res.LastInsertId()
	lwutil.CheckError(err, "")

	// reply
	type Reply struct {
		Userid int64
	}
	lwutil.WriteResponse(w, Reply{id})
}

func login(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
	lwutil.CheckMathod(r, "POST")

	// input
	type Input struct {
		Username  string
		Password  string
		Appsecret string
	}
	var input Input
	lwutil.DecodeRequestBody(r, &input)

	if input.Username == "" || input.Password == "" {
		lwutil.SendError("err_input", "")
	}

	pwsha := lwutil.Sha224(input.Password + passwordSalt)

	// get userid
	row := authDB.QueryRow("SELECT id FROM user_accounts WHERE username=? AND password=?", input.Username, pwsha)
	var userid uint64
	err := row.Scan(&userid)
	lwutil.CheckError(err, "err_not_match")

	// get appid
	appid := uint32(0)
	if input.Appsecret != "" {
		row = authDB.QueryRow("SELECT id FROM apps WHERE secret=?", input.Appsecret)
		err = row.Scan(&appid)
		lwutil.CheckError(err, "err_app_secret")
	}

	// new session
	rc := redisPool.Get()
	defer rc.Close()

	usertoken, err := newSession(w, rc, userid, input.Username, appid)
	lwutil.CheckError(err, "")

	// reply
	type Reply struct {
		Usertoken string
		Appid     uint32
	}
	reply := Reply{usertoken, appid}
	lwutil.WriteResponse(w, reply)
}

func logout(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
	lwutil.CheckMathod(r, "POST")

	session, err := findSession(w, r)
	lwutil.CheckError(err, "err_already_logout")

	usertokenCookie, err := r.Cookie("usertoken")
	lwutil.CheckError(err, "err_already_logout")
	usertoken := usertokenCookie.Value

	rc := redisPool.Get()
	defer rc.Close()

	rc.Send("del", fmt.Sprintf("sessions/%s", usertoken))
	rc.Send("del", fmt.Sprintf("usertokens/%d+%d", session.Userid, session.Appid))
	rc.Flush()
	for i := 0; i < 2; i++ {
		_, err = rc.Receive()
		lwutil.CheckError(err, "")
	}

	// reply
	lwutil.WriteResponse(w, "logout")
}

func newApp(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
	lwutil.CheckMathod(r, "POST")

	session, err := findSession(w, r)
	lwutil.CheckError(err, "err_auth")
	checkAdmin(session)

	// input
	type Input struct {
		Name string
	}
	var input Input
	lwutil.DecodeRequestBody(r, &input)

	if input.Name == "" {
		lwutil.SendError("err_input", "input.Name empty")
	}

	// db
	stmt, err := authDB.Prepare("INSERT INTO apps (name, secret) VALUES (?, ?)")
	lwutil.CheckError(err, "")

	secret := lwutil.GenUUID()
	_, err = stmt.Exec(input.Name, secret)
	lwutil.CheckError(err, "err_name_exists")

	// reply
	type Reply struct {
		Name   string
		Secret string
	}
	reply := Reply{input.Name, secret}
	lwutil.WriteResponse(w, reply)
}

func listApp(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
	lwutil.CheckMathod(r, "POST")

	session, err := findSession(w, r)
	lwutil.CheckError(err, "err_auth")
	checkAdmin(session)

	// db
	rows, err := authDB.Query("SELECT name, secret FROM apps")
	lwutil.CheckError(err, "")

	type App struct {
		Name   string
		Secret string
	}

	apps := make([]App, 0, 16)
	var app App
	for rows.Next() {
		err = rows.Scan(&app.Name, &app.Secret)
		lwutil.CheckError(err, "")
		apps = append(apps, app)
	}

	lwutil.WriteResponse(w, apps)
}

func info(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
	lwutil.CheckMathod(r, "POST")

	session, err := findSession(w, r)
	lwutil.CheckError(err, "err_auth")

	//
	usertokenCookie, err := r.Cookie("usertoken")
	usertoken := usertokenCookie.Value

	//
	type Reply struct {
		Session   *Session
		UserToken string
	}
	reply := Reply{session, usertoken}

	lwutil.WriteResponse(w, reply)
}

func regAuth() {
	http.HandleFunc("/auth/login", login)
	http.HandleFunc("/auth/logout", logout)
	http.HandleFunc("/auth/register", register)
	http.HandleFunc("/auth/newapp", newApp)
	http.HandleFunc("/auth/listapp", listApp)
	http.HandleFunc("/auth/info", info)
}
