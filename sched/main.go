package main

import (
	// "github.com/golang/glog"
	"fmt"
	"flag"
)

func main() {
	flag.Parse()
	go pvpMain()
	go sandRewardMain()
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
