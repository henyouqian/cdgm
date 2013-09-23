package main

import (
	"encoding/json"
	"github.com/henyouqian/lwutil"
	"io/ioutil"
	"os"
	"strings"
	//"github.com/golang/glog"
)

func parseMaps() error {
	type Layer struct {
		Name string
		//Data []uint8
	}
	type Zone struct {
		Width  uint32
		Height uint32
		Layers []Layer
	}
	dir := "../data/map"
	files, _ := ioutil.ReadDir(dir)
	for _, f := range files {
		s := strings.Split(f.Name(), ".")
		if s[1] == "json" {
			filepath := dir + "/" + f.Name()
			pf, err := os.Open(filepath)
			if err != nil {
				return lwutil.NewErr(err)
			}
			defer pf.Close()
			dec := json.NewDecoder(pf)
			var zone Zone
			dec.Decode(&zone)
		}

	}
	return nil
}

func genCache(zoneid uint32, isLastZone bool) {

}

func regZone() {

}
