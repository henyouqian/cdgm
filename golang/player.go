package main

import (
	_ "github.com/go-sql-driver/mysql"
)

type ItemPack struct {
	Id    uint8
	Count uint16
}

func addItems(userId uint32, items []ItemPack) {
	//row, err := db.QueryRow("SELECT items FROM playerInfos WHERE ")
	//checkErr(err)

	//for rows.Next() {
	//	var uid int
	//	var username string
	//	var department string
	//	var created string
	//	err = rows.Scan(&uid, &username, &department, &created)
	//	checkErr(err)
	//	fmt.Println(uid)
	//	fmt.Println(username)
	//	fmt.Println(department)
	//	fmt.Println(created)
	//}
}
