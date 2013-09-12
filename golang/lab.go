package main

import (
	"fmt"
	"github.com/henyouqian/lwUtil"
	"net/http"
)

func dbSimple(w http.ResponseWriter, r *http.Request) {
	defer lwutil.HandleError(w)
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
	defer lwutil.HandleError(w)
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
	http.HandleFunc("/lab/dbsimple", dbSimple)
	http.HandleFunc("/lab/dbbatch", dbBatch)
}
