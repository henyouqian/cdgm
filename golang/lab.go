package main

import (
	"fmt"
	"net/http"
)

func dbSimple(w http.ResponseWriter, r *http.Request) {
	defer handleError(w)
	checkMathod(r, "GET")

	// db
	ids := make([]int64, 10)
	stmt, err := testDB.Prepare("INSERT INTO batchTest (a, b, c, d) VALUES (?, ?, ?, ?)")
	checkError(err, "")
	for i := 0; i < 10; i++ {
		res, err := stmt.Exec(1, 2, 3, 4)
		checkError(err, "")

		id, err := res.LastInsertId()
		checkError(err, "")

		ids[i] = id
	}

	writeResponse(w, ids)
}

func dbBatch(w http.ResponseWriter, r *http.Request) {
	defer handleError(w)
	checkMathod(r, "GET")

	// db
	ids := make([]int64, 10)
	tx, err := testDB.Begin()
	checkError(err, "")
	stmt, err := tx.Prepare("INSERT INTO batchTest (a, b, c, d) VALUES (?, ?, ?, ?)")
	checkError(err, "")
	for i := 0; i < 10; i++ {
		res, err := stmt.Exec(1, 2, 3, 4)
		checkError(err, "")

		id, err := res.LastInsertId()
		checkError(err, "")

		ids[i] = id

		fmt.Println(id)
	}

	writeResponse(w, ids)

	err = tx.Commit()
	checkError(err, "")
}

func regLab() {
	http.HandleFunc("/lab/dbsimple", dbSimple)
	http.HandleFunc("/lab/dbbatch", dbBatch)
}
