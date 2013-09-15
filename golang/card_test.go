package main

import (
	"testing"
)

func TestCalcCardAttr(t *testing.T) {
	testDatas := []struct {
		protoId uint32
		level   uint16
		attr    cardAttr
	}{
		{101, 1, cardAttr{530, 670, 520, 430, 450}},
		{101, 30, cardAttr{2120, 2680, 2070, 1740, 1790}},
	}

	for _, data := range testDatas {
		attr, _ := calcCardAttr(data.protoId, data.level)
		if *attr != data.attr {
			t.Errorf("%v != %v", attr, data.attr)
		}
	}
}
