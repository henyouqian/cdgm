package main

import (
	"fmt"
	////"github.com/golang/glog"
	"github.com/henyouqian/lwUtil"
	//"strconv"
	//"strings"
)

type wagonCardInfo struct {
	id    uint64
	proto uint32
}

func wagonAddCards(wagonIdx uint8, userId uint32, cardInfos []wagonCardInfo, desc string) error {
	if len(cardInfos) == 0 {
		return lwutil.NewErrStr("no cards")
	}
	if wagonIdx > WAGON_IDX_MAX {
		return lwutil.NewErrStr("wagonIdx error")
	}

	//db
	err := func() error {
		//setup transaction
		tx, err := whDB.Begin()
		if err != nil {
			return lwutil.NewErr(err)
		}
		defer lwutil.EndTx(tx, &err)

		//insert into wagons
		stmt, err := tx.Prepare(`INSERT INTO wagons
            (userId, wagonIdx, count, cardEntity, cardProto, descText)
			VALUES(?, ?, ?, ?, ?, ?)`)
		if err != nil {
			return lwutil.NewErr(err)
		}

		for _, cardInfo := range cardInfos {
			_, err := stmt.Exec(userId, wagonIdx, 1, cardInfo.id, cardInfo.proto, desc)
			if err != nil {
				return lwutil.NewErr(err)
			}
		}

		//update userinfo
		cols := []string{"wagonGeneral", "wagonTemp", "wagonSocial"}
		sql := fmt.Sprintf(`UPDATE playerInfos SET %s=%s+?
			WHERE userId=?`, cols[wagonIdx], cols[wagonIdx])
		tx.Exec(sql, len(cardInfos), userId)

		return nil
	}()
	if err != nil {
		return lwutil.NewErr(err)
	}

	return nil
}

type wagonItemInfo struct {
	id    uint8
	count uint16
}

func wagonAddItems(wagonIdx uint8, userId uint32, items []wagonItemInfo, desc string) error {
	if len(items) == 0 {
		return lwutil.NewErrStr("no items")
	}
	if wagonIdx > WAGON_IDX_MAX {
		return lwutil.NewErrStr("wagonIdx error")
	}

	//db
	err := func() error {
		//setup transaction
		tx, err := whDB.Begin()
		if err != nil {
			return lwutil.NewErr(err)
		}
		defer lwutil.EndTx(tx, &err)

		return nil
	}()
	if err != nil {
		return lwutil.NewErr(err)
	}

	return nil
}
