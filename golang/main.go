package main

import (
	"flag"
	"fmt"
	"github.com/golang/glog"
	"github.com/henyouqian/lwUtil"
	"net/http"
	"runtime"
)

func staticFile(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, r.URL.Path[1:])
}

func test() {
	glog.Infoln(tblCard["101"])
	cardAttr, _ := calcCardAttr(101, 10)
	glog.Infoln(cardAttr)

	type ccc struct {
		Age  int
		Name string
	}
	s := ccc{12, "fsdf"}
	k, v, err := lwutil.GetStructFieldKVs(s)
	glog.Infoln(k, v, err)
}

func main() {
	var port int
	flag.IntVar(&port, "port", 9999, "server port")
	flag.Parse()

	http.HandleFunc("/static/", staticFile)

	regAuth()
	regLab()

	test()

	runtime.GOMAXPROCS(runtime.NumCPU())

	glog.Infof("Server running: cpu=%d, port=%d", runtime.NumCPU(), port)
	glog.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}
