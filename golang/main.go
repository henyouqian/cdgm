package main

import (
	"flag"
	"fmt"
	"github.com/golang/glog"
	"github.com/henyouqian/lwutil"
	"net/http"
	"runtime"
)

func staticFile(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, r.URL.Path[1:])
}

func test() {
	glog.Infoln(tblCard["101"])
	cardAttr, _ := calcCardAttr(101, 1)
	glog.Infoln(cardAttr)

	type ccc struct {
		Age  int
		Name string
	}
	s := ccc{12, "fsdf"}
	k, v, err := lwutil.GetStructFieldKVs(s)
	glog.Infoln(k, v, err)

	a := make(map[int]*ccc)
	a[1] = &ccc{111, "aaa"}
	a[1].Age = 45
	glog.Infoln(a[1])

	//protoAndLvs := []cardProtoAndLevel{cardProtoAndLevel{333, 15}}
	//cards, err := createCards(12, protoAndLvs, 100, 0, "hahahaha")
	//glog.Infoln(cards[0], err)

	items := []ItemInfo{{8, 111}, {10, 222}}
	wagonAddItems(0, 12, items, "iiiiitems")
}

func main() {
	var port int
	flag.IntVar(&port, "port", 9001, "server port")
	flag.Parse()

	http.HandleFunc("/static/", staticFile)

	//shit code
	lwutil.HttpCodeInternalServerError = http.StatusOK
	lwutil.HttpCodeBadRequest = http.StatusOK

	//reg
	regLab()
	regAuth()
	regStore()
	regNews()
	regInstance()
	regZone()
	regCard()
	regPlayer()
	regGameEvent()
	regAdmin()

	lab()

	runtime.GOMAXPROCS(runtime.NumCPU())

	glog.Infof("Server running: cpu=%d, port=%d", runtime.NumCPU(), port)
	glog.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}
