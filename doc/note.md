* 永久性的数据不要存在redis，redis存的数据要么设置TTL，要么数据上限是可预见的，要么有程序定期清理
* mysql的transaction部分能保证同一个连接，但是真正的transaction吗
* 某些地方是不是要加行锁，比如使用一个物品，现实select到物品的数量，看是不是大于0，大于0就使用，然后update物品数量。如果在update物品数量之前，又有一条select选了同一个物品，这时看到的数量是没有减过的。当物品剩下最后一个时，这样会成功使用两次这个物品。改成用存储过程吧。
* setband要验证必须有主角存在
* 注意在地图中的角色，也就是zoneCache中band里面的角色，不能evolution 吃卡之类的
* band的数量不是固定的3组
* cards.csv 分成了cards.csv和monsterCards.csv两部分，怪物的数据要从csv和monsterCards.csv读
* move 中捡到大小钱袋的具体数值
* 对卡片的操作不要只简单的限制在地图中就禁止。只禁止在band中的不能操作


* redis服务器要单独配置，需要大内存
* 凡是得到卡片的消息，例如card/getpact，zone/battleresult,都要标明是否有卡片放入wagon

* getpact请求发生过一次锁定。
Traceback (most recent call last):
  File "/home/wh/cdgm/card.py", line 281, in get
    cards = yield create_cards(user_id, card_ids, max_card_num, 1)
GeneratorExit

应该是create_cards没返回。create_cards中的yield全部和数据库操作相关，而且用了transaction。我怀疑是没执行完，数据库被锁。考虑用存储过程替换。
