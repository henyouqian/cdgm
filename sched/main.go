package main

import (
	// "github.com/golang/glog"
	"fmt"
)

func main() {
	go pvpMain()
	var input string
	for {
		fmt.Print(">>")
		fmt.Scanln(&input)
		if input == "quit" {
			break
		}
		fmt.Println(input)
	}
}
