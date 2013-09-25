package main

import (
	"fmt"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"sort"
)

func dbSimple(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	// db
	ids := make([]int64, 10)
	stmt, err := testDB.Prepare("INSERT INTO batchTest (a, b, c, d) VALUES (?, ?, ?, ?)")
	lwutil.CheckError(err, "")
	for i := 0; i < 10; i++ {
		res, err := stmt.Exec(1, 2, 3, 4)
		lwutil.CheckError(err, "")

		id, err := res.LastInsertId()
		lwutil.CheckError(err, "")

		ids[i] = id
	}

	lwutil.WriteResponse(w, ids)
}

func dbBatch(w http.ResponseWriter, r *http.Request) {
	lwutil.CheckMathod(r, "GET")

	// db
	ids := make([]int64, 10)
	tx, err := testDB.Begin()
	lwutil.CheckError(err, "")
	stmt, err := tx.Prepare("INSERT INTO batchTest (a, b, c, d) VALUES (?, ?, ?, ?)")
	lwutil.CheckError(err, "")
	for i := 0; i < 10; i++ {
		res, err := stmt.Exec(1, 2, 3, 4)
		lwutil.CheckError(err, "")

		id, err := res.LastInsertId()
		lwutil.CheckError(err, "")

		ids[i] = id

		fmt.Println(id)
	}

	lwutil.WriteResponse(w, ids)

	err = tx.Commit()
	lwutil.CheckError(err, "")
}

func regLab() {
	http.Handle("/lab/dbsimple", lwutil.ReqHandler(dbSimple))
	http.Handle("/lab/dbbatch", lwutil.ReqHandler(dbBatch))
}

func g() {
	glog.Infoln("g")
}

func s() {
	l := []int{3, 35, 23, 6, 22}
	sort.Sort(sort.Reverse(sort.IntSlice(l)))
	glog.Infoln(l)
}

func lab() {

}
