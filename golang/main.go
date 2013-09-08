package main

import (
	"flag"
	"fmt"
	"github.com/golang/glog"
	"net/http"
	"runtime"
)

func staticFile(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, r.URL.Path[1:])
}

func main() {
	var port int
	flag.IntVar(&port, "port", 9999, "server port")
	flag.Parse()

	http.HandleFunc("/static/", staticFile)

	regAuth()
	regLab()

	runtime.GOMAXPROCS(runtime.NumCPU())

	glog.Infof("Server running: cpu=%d, port=%d", runtime.NumCPU(), port)
	glog.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}
