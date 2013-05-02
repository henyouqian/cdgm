Server Side Api (ver0.1 Draft)
=============================
## 共有Error
	error == "": 成功.
	error == "err_param": 参数错误.
	error == "err_auth": 身份验证错误，没登陆或者token超时.
	error == "err_internal": 服务器内部错误.
	
## 所有的whapi下的接口都需要带上token参数，比如
- 		{ServerURL}/whapi/player/getinfo?token=16995a9581c74b18ad1584ad9c68d245
- 		{ServerURL}/whapi/player/create?warlord=3&token=16995a9581c74b18ad1584ad9c68d245

## 测试server: 42.121.107.155

--------------------------------------------
## authapi/register
- Method: GET
- Desc: 注册帐号
- Param:
-		username = {STRING(40)}
		password = {STRING(40)}
- Example: 
- 		{ServerURL}/authapi/register?username=foo&password=bar123
- Return:
-		{
			error: {STRING}	/* 错误 */
			token: {STRING}	/* 用户token，用于后续会话的身份验证。（同名cookie里有同样的信息） */
		}
		error == "err_account_exist": 用户名已存在.

## authapi/login
- Method: GET
- Desc: 用户登入
- Param:
-		username = {STRING(40)}
		password = {STRING(40)}
- Example: 
- 		{ServerURL}/authapi/login?username=foo&password=bar123
- Return:
-		{
			error: {STRING},	/* 错误 */
			token: {STRING}	/* 用户token，用于后续会话的身份验证。（同名cookie里有同样的信息） */
			playerExist: {BOOL} /* 用户的角色是否已经创建 */
		}
		error == "err_not_match": 用户名与密码不匹配，即用户名未注册或者密码错误.
		
## whapi/player/create
- Method: GET
- Desc: 选主角，初始化玩家信息
- Param: 
- 		warlord = {INT}		/* 0-7 */
- Example:
- 		{ServerURL}/whapi/player/create?warlord=3&token=16995a9581c74b18ad1584ad9c68d245
- Return: 
- 		{
			error: {STRING},    	/* 错误 */
		}
		error == "err_player_exist": player已存在
		error == "err_create_warlord": warlord创建失败

## whapi/player/getinfo
- Method: GET
- Desc: 获取当前登入玩家的信息
- Param: 无
- Example: 
- 		{ServerURL}/whapi/player/getinfo?token=16995a9581c74b18ad1584ad9c68d245
- Return: 
-		{
			error: {STRING},    	/* 错误 */
			userId: {INT},			/* 用户ID */
			name: {STRING},			/* 用户名称 */
			warload: {INT},			/* 主角卡ID */
			money: {INT},			/* 钱 */
			inZoneId: {INT},    	/* 如果已进入zone返回zoneId，否则返回0 */
			lastZoneId: {INT}, 		/* 已解锁的地图的最后ID */
			ap: {INT},				/* 当前行动值，用于推图 */
			maxAp: {INT},			/* 最大行动值 */
			apAddRemain: {INT},		/* 距下次增加ap时间（秒） */
			xp: {INT},				/* 当前活动行动值，用于pvp，boss战等 */
			maxXp: {INT},			/* 最大活动行动值 */
			xpAddRemain: {INT},		/* 距下次增加xp时间（秒） */
			lastFormation: {INT}	/* 最新得到的阵形 */
			currentBand: {INT}		/* 当前选择band index, 从0开始*/
			cards: 	[				/* 当前用户拥有的卡片信息，为cardEntity对象的数组*/
						{
							id: {INT},			/* 实体id（流水号） */
							protoId: {INT},		/* 原型id（卡片类型） */
							level: {INT},		/* 等级 */
							exp: {INT},			/* 经验值 */
							hp: {INT},			/* 基础hp */
							atk: {INT},			/* 基础atk */
							def: {INT},			/* 基础def */
							wis: {INT},			/* 基础wis */
							agi: {INT},			/* 基础agi */
							hpCrystal: {INT},	/* 水晶增加的hp */
							atkCrystal: {INT},	/* 水晶增加的atk */
							defCrystal: {INT},	/* 水晶增加的def */
							wisCrystal: {INT},	/* 水晶增加的wis */
							agiCrystal: {INT},	/* 水晶增加的agi */
							hpExtra: {INT},		/* 进化增加的hp */
							atkExtra: {INT},	/* 进化增加的atk */
							defExtra: {INT},	/* 进化增加的def */
							wisExtra: {INT},	/* 进化增加的wis */
							agiExtra: {INT},	/* 进化增加的agi */
							skillLevel: {INT},	/* 技能等级 */
							skillExp: {INT},	/* 技能经验值 */
							addSkill1: {INT},	/* 附加技能 */
							addSkill2: {INT}	/* 附加技能2 */
						},
						... 
			], 
			bands: 	[							/* band信息 *
						{
							index: {INT},		/* band index,区间为[0,2] */
							formation: {INT}, 	/* 阵形id */
							members: [{INT or null}, ...]	/* band 成员，使用cardEntityId.空位用null.数量必须与阵形匹配 */
						},
						...
			],		
			items:	[							/* item信息 */
						{ 
							id: {INT},		/* item id */
							num: {INT} 		/* item 数量 */
						},		
						...
			]
		}
		error == "err_player_not_exist": player未创建
		
## whapi/player/setband
- Method: POST
- Desc: 设置band
- Input:
- 		[
			{
				index: {INT},		/* band index,区间为[0,2] */
				formation: {INT}, 	/* 阵形id */
				members: [{INT or null}, ...]	/* 成员，使用cardEntityId.空位用null.数量必须与阵形匹配 */
			}
			...
		]
- Example: 
-		[
			{"index":0, "formation":23, "members":[34, 643, null, 456, null, 54]},
			{"index":2, "formation":25, "members":[454, 543, 43, 37, 77, 54]}
		]
- Return: 
- 		{
 			error: {STRING},   	/* 错误 */
		}
		

## whapi/player/useitem
- Method: GET
- Desc: 使用物品
- Param:
-		itemid = {INT}
- Example: 
-		{ServerURL}/whapi/player/useitem?itemid=1&token=16995a9581c74b18ad1584ad9c68d245
- Return: 
- 		{
 			error: {STRING},   	/* 错误 */
								/* err_not_exist: 物品不存在（数量为0） */
								/* err_param: 参数错误*/
								/* err_db: 数据库错误*/
			itemId: {INT},		/* 被使用物品 */
			itemNum: {INT},		/* 物品剩余数量 */
		}
		


## whapi/zone/enter
- Method: GET
- Desc: 获取当前地图信息
- Param: 
- 		zoneid = {INT}		/* 地图id *
		bandidx = {INT}		/* 指定使用第几个band， 从0开始 */
- Example: {ServerURL}/whapi/zone/enter?zoneid=10&bandidx=0&token=16995a9581c74b18ad1584ad9c68d245
- Return: 
- 		{
 			error: {STRING},   				/* 错误 */
			zoneId: {INT}, 					/* 当前的Zone ID */
			startPos: {x:{INT}, y:{INT}},	/* 起点位置 */
			goalPos: {x:{INT}, y:{INT}},	/* 终点位置 */
			currPos: {x:{INT}, y:{INT}},	/* 当前位置 */
			redCase: {int}					/* 红宝箱获得数量 */
			goldCase: {int}					/* 金宝箱获得数量 */
			objs: [
				[
				
					{INT}, 		/* x坐标 */
				 	{INT}, 		/* y坐标 */
					{INT}		/* 类型 */
									/* 1:木箱 */
									/* 2:红宝箱 */
									/* 3:金宝箱 */
									/* 4:小钱袋 */
									/* 5:大钱袋 */
									/* 6:pvp */
									/* <0:绝对值为Monster Group的id */
									/* >10000:事件(暂定) */
				], 
				...
			]
			band: {
				formation: {INT}	/* 阵形id */
				members: [
					{
						id: {INT}, 
						hp: {INT}
					}, /* id为CardEntityId, hp为该Card的当前血量*/ 
					...
				]
			}
		}


## whapi/zone/get
- Method: GET
- Desc: 获取当前进入的地图的游戏数据
- Input: 无
- Example: {ServerURL}/whapi/zone/get?token=16995a9581c74b18ad1584ad9c68d245
- Return: 
- 		{
 			error: {STRING},   	/* 错误 */
			zoneId: {INT}, 		/* 当前的Zone ID */
			startPos: {x:{INT}, y:{INT}},	/* 起点位置 */
			goalPos: {x:{INT}, y:{INT}},	/* 终点位置 */
			currPos: {x:{INT}, y:{INT}},	/* 当前位置 */
			redCase: {int}					/* 红宝箱获得数量 */
			goldCase: {int}					/* 金宝箱获得数量 */
			objs: [
				[
				
					{INT}, 		/* x坐标 */
				 	{INT}, 		/* y坐标 */
					{INT}		/* 类型 */
									/* 1:木箱 */
									/* 2:红宝箱 */
									/* 3:金宝箱 */
									/* 4:小钱袋 */
									/* 5:大钱袋 */
									/* 6:pvp */
									/* <0:绝对值为Monster Group的id */
									/* >10000:事件(暂定) */
				], 
				...
			]
			band: {
				formation: {INT}	/* 阵形id */
				members: [
					{
						id: {INT}, 
						hp: {INT}
					}, /* id为CardEntityId, hp为该Card的当前血量*/ 
					...
				]
			}
		}

## whapi/zone/withdraw
- Method: GET
- Desc: 退出zone
- Param: 无
- Example: {ServerURL}/whapi/zone/withdraw?token=16995a9581c74b18ad1584ad9c68d245
- Return: 
- 		{
 			error: {STRING},   	/* 错误 */
		}

## whapi/zone/move
- Method: POST
- Desc: 在地图中移动
- Param:
-		[					/* 顺序走过的所有坐标 */
			[INT, INT]，		/* xy坐标 */
			[INT, INT]			
		]
- Example: {ServerURL}/whapi/zone/move?x=10&y=17
- Return: 
- 		{
			error: {STRING},		/* 错误 */
			currPos: [{INT}, {INT}],/* 地图中的当前位置 */
			xp: {INT},				/* 当前行动值 */
			nextAddXpTime: {INT},	/* 距下次加xp还有几秒 */
			moneyAdd: {INT},		/* 获得的money */
			redCaseAdd: {INT},		/* 获得的红宝箱数量（0或1） */
			goldCaseAdd: {INT},		/* 获得的金宝箱数量（0或1） */
			items: [				/* 获得item */
				{
					id: {INT},		/* 获得item类型 */
					num": {INT}		/* 获得item数量 */
				},
				...
			],
			
			eventId: {INT}, 		/* 当前格子的event id */
		}

## whapi/zone/battleresult
- Method: POST
- Desc: 获得Battle 的结果
- Input: 
- 		{
			isWin: {BOOL}, 		/* 战斗是否胜利 */
			members: [
				{
					id: {INT},
					hp: {INT}
				}, /* id为CardEntityId, hp为该Card的当前血量*/ 
				...
			]
			catchCards: [{INT}, {INT} ...], /* fixme:未实现 捕获的新的卡 */
			consumeItems: [{INT}, ... ]		/* fixme:未实现 使用的ITEM ID */
		}
- Example: 
		{ServerURL}/whapi/zone/battleresult?token=16995a9581c74b18ad1584ad9c68d245
		
		{"isWin":true,"members":[null,{"hp":1743,"id":119},null]}
		
- Return: 
- 		{
			error : {STRING}  		/* 通用格式，如果为空字符串，则为正确 */
			members: [				/* 成员更新经验值 */
				{
					id: {INT},		/* card entity id */
					exp: {INT}，		/* 更新后的经验值 */
				},
				...
			]
			levelups: [				/* 升级了的成员 */
				{
					id: {INT}, 		/* card entity id */
					level: {INT}，	/* 更新后的等级 */
				}
			]
		}

## whapi/zone/complete
- Method: GET
- Desc: 完成当前地图
- Param: 无
- Example: {ServerURL}/whapi/zone/complete
- Return: 
- 		{
			error: {STRING}  /* 通用格式，如果为空字符串，则为正确 */
			redCase: [					/* 开红宝箱获得item */
				{
					id:{INT},			/* 获得item类型 */
					num: {INT}			/* 获得item数量 */
				},
				...
			],
			goldCase: [					/* 开金宝箱获得item */
				{
					id:{INT},			/* 获得item类型 */
					num: {INT}			/* 获得item数量 */
				},
				...
			],
			lastZoneId: {INT}, 			/* 最新解锁的地图ID */
		}

## whapi/card/getpact
- Method: GET
- Desc: 抽卡
- Param:
		packid = {INT} 		/* 卡包的id */
		num = {INT}			/* 抽卡次数，只有当消耗物品不为whCoin才起作用, 目前上限暂定为10 */
- Example: {ServerURL}/whapi/card/getpact?packid=7&num=5&token=16995a9581c74b18ad1584ad9c68d245
- Return: 
- 		{
 			error: {STRING},   	/* 错误 */
			cards: 	[				/* 当前用户拥有的卡片信息，为cardEntity对象的数组*/
						{
							id: {INT},			/* 实体id（流水号） */
							protoId: {INT},		/* 原型id（卡片类型） */
							level: {INT},		/* 等级 */
							exp: {INT},			/* 经验值 */
							hp: {INT},			/* 基础hp */
							atk: {INT},			/* 基础atk */
							def: {INT},			/* 基础def */
							wis: {INT},			/* 基础wis */
							agi: {INT},			/* 基础agi */
							hpCrystal: {INT},	/* 水晶增加的hp */
							atkCrystal: {INT},	/* 水晶增加的atk */
							defCrystal: {INT},	/* 水晶增加的def */
							wisCrystal: {INT},	/* 水晶增加的wis */
							agiCrystal: {INT},	/* 水晶增加的agi */
							hpExtra: {INT},		/* 进化增加的hp */
							atkExtra: {INT},	/* 进化增加的atk */
							defExtra: {INT},	/* 进化增加的def */
							wisExtra: {INT},	/* 进化增加的wis */
							agiExtra: {INT},	/* 进化增加的agi */
							skillLevel: {INT},	/* 技能等级 */
							skillExp: {INT},	/* 技能经验值 */
							addSkill1: {INT},	/* 附加技能 */
							addSkill2: {INT}	/* 附加技能2 */
						},
						... 
			]
		}

## whapi/card/sell
- Method: POST
- Desc: 卖卡给系统，得到money
- Input:
		[
			{INT},	/* 卡的entity id */
			...
		]

- Example: {ServerURL}/whapi/card/sell?token=16995a9581c74b18ad1584ad9c68d245
		[345, 66, 7456, 74567, 45235]
- Return: 
- 		{
 			error: {STRING},   		/* 错误 */
			cardIds: [{INT}, ...],	/* 卡片id数组，同post数据 */
			money:{INT},			/* 最新money数量 */
			moneyAdd: {INT},		/* 增加的money数量 */
		}

## whapi/card/evolution
- Method: GET
- Desc: 进化
- Param:
		cardid1 = {INT}		/* 主卡id */
		cardid2 = {INT}		/* 副卡id */

- Example: {ServerURL}/whapi/card/evolution?cardid1=3455&cardid2=45678&token=16995a9581c74b18ad1584ad9c68d245
		
- Return: 
- 		{
 			error: {STRING},   		/* 错误 */
			money:{INT},			/* 最新money数量 */
			delCardId: {INT},		/* 副卡ID（被吃的卡） */
			evoCard: {				/* 进化后的主卡 */
							id: {INT},			/* 实体id（流水号） */
							protoId: {INT},		/* 原型id（卡片类型） */
							level: {INT},		/* 等级 */
							exp: {INT},			/* 经验值 */
							hp: {INT},			/* 基础hp */
							atk: {INT},			/* 基础atk */
							def: {INT},			/* 基础def */
							wis: {INT},			/* 基础wis */
							agi: {INT},			/* 基础agi */
							hpCrystal: {INT},	/* 水晶增加的hp */
							atkCrystal: {INT},	/* 水晶增加的atk */
							defCrystal: {INT},	/* 水晶增加的def */
							wisCrystal: {INT},	/* 水晶增加的wis */
							agiCrystal: {INT},	/* 水晶增加的agi */
							hpExtra: {INT},		/* 进化增加的hp */
							atkExtra: {INT},	/* 进化增加的atk */
							defExtra: {INT},	/* 进化增加的def */
							wisExtra: {INT},	/* 进化增加的wis */
							agiExtra: {INT},	/* 进化增加的agi */
							skillLevel: {INT},	/* 技能等级 */
							skillExp: {INT},	/* 技能经验值 */
							addSkill1: {INT},	/* 附加技能 */
							addSkill2: {INT}	/* 附加技能2 */
			}
		}

## whapi/card/sacrifice
- Method: POST
- Desc: 献祭，加技能属性
- Input:
		[{INT}, ...]	/* 第一张为主卡，后面的全为用来献祭的卡 */

- Example: {ServerURL}/whapi/card/sacrifice?token=16995a9581c74b18ad1584ad9c68d245
		[34444, 5456, 74567, 8768, 32534]

- Return: 
- 		{
 			error: {STRING},   			/* 错误 */
			money:{INT},				/* 最新money数量 */
			sacrificers: [{INT}, ...]	/* 献祭掉的卡的id数组 */
			master: {					/* 加了技能点后的主卡 */ fixme；不需要这么多信息
							id: {INT},			/* 实体id（流水号） */
							protoId: {INT},		/* 原型id（卡片类型） */
							level: {INT},		/* 等级 */
							exp: {INT},			/* 经验值 */
							hp: {INT},			/* 基础hp */
							atk: {INT},			/* 基础atk */
							def: {INT},			/* 基础def */
							wis: {INT},			/* 基础wis */
							agi: {INT},			/* 基础agi */
							hpCrystal: {INT},	/* 水晶增加的hp */
							atkCrystal: {INT},	/* 水晶增加的atk */
							defCrystal: {INT},	/* 水晶增加的def */
							wisCrystal: {INT},	/* 水晶增加的wis */
							agiCrystal: {INT},	/* 水晶增加的agi */
							hpExtra: {INT},		/* 进化增加的hp */
							atkExtra: {INT},	/* 进化增加的atk */
							defExtra: {INT},	/* 进化增加的def */
							wisExtra: {INT},	/* 进化增加的wis */
							agiExtra: {INT},	/* 进化增加的agi */
							skillLevel: {INT},	/* 技能等级 */
							skillExp: {INT},	/* 技能经验值 */
							addSkill1: {INT},	/* 附加技能 */
							addSkill2: {INT}	/* 附加技能2 */
			}
		}

## whapi/wagon/list
- Method: GET
- Desc: 列出wagon中的物品
- Param:
-		wagonidx = {INT[,INT][,INT]}		/* 0:general 1:temp 2:social 可以同时取多个，用逗号隔开 */

- Example: 
-		{ServerURL}/whapi/wagon/list?type=0,1,2&token=16995a9581c74b18ad1584ad9c68d245

- Return: 
- 		{
 			error: {STRING},   			/* 错误 */
			wagons:[
				{
					wagonIdx: {INT},			/* 0:general 1:temp 2:social */
					objs:[						/* 物品列表，分item和card两种 */
						{						/* 这是item */
							key: {STRING}		/* key */
							itemId: {INT}		/* 物品id */
							itemNum: {INT}		/* 物品数量 */
							time: {STRING}		/* 放入时间 */
						}
						or
						{						/* 这是card */
							key: {STRING}		/* key */
							cardEntity: {INT}	/* 卡片实例id */
							cardProto: {INT}	/* 卡片原型id */
							time: {STRING}		/* 放入时间 */
						}
						...
					]
				}
				...
			]
		}

## whapi/wagon/accept
- Method: GET
- Desc: 取出物品
- Param:
-		wagonidx = {INT}			/* 0:general 1:temp 2:social 可以同时取多个，用逗号隔开 */
		key = {STRING}(optional)	/* 指定要取出的物品，假如没有这个参数，取出这个wagon中的所有物品 */
- Example: 
-		{ServerURL}/whapi/wagon/accept?wagonidx=1&itemidx=card:383&token=16995a9581c74b18ad1584ad9c68d245
		{ServerURL}/whapi/wagon/accept?wagonidx=1 /* accept all */
- Return:
- 		{
 			error: {STRING},   			/* 错误 */
			wagonIdx: {INT},			/* 0:general 1:temp 2:social */
			delKeys: [INT, ...],		/* 物品的key，用来找到并删除*/
			items: [
				{
					id: {INT},	 		/* item类型 */
					num: {INT}			/* item数量 */
				},
				...
			]
			cards: [
				{					
					id: {INT},			/* 实体id（流水号） */
					protoId: {INT},		/* 原型id（卡片类型） */
					level: {INT},		/* 等级 */
					exp: {INT},			/* 经验值 */
					hp: {INT},			/* 基础hp */
					atk: {INT},			/* 基础atk */
					def: {INT},			/* 基础def */
					wis: {INT},			/* 基础wis */
					agi: {INT},			/* 基础agi */
					hpCrystal: {INT},	/* 水晶增加的hp */
					atkCrystal: {INT},	/* 水晶增加的atk */
					defCrystal: {INT},	/* 水晶增加的def */
					wisCrystal: {INT},	/* 水晶增加的wis */
					agiCrystal: {INT},	/* 水晶增加的agi */
					hpExtra: {INT},		/* 进化增加的hp */
					atkExtra: {INT},	/* 进化增加的atk */
					defExtra: {INT},	/* 进化增加的def */
					wisExtra: {INT},	/* 进化增加的wis */
					agiExtra: {INT},	/* 进化增加的agi */
					skillLevel: {INT},	/* 技能等级 */
					skillExp: {INT},	/* 技能经验值 */
					addSkill1: {INT},	/* 附加技能 */
					addSkill2: {INT}	/* 附加技能2 */
				},
				...
			]
		}

## whapi/wagon/sellall
- Method: GET
- Desc: 取出物品
- Param:
-		wagonidx = {INT}			/* 0:general 1:temp 2:social 可以同时取多个，用逗号隔开 */
- Example: 
-		{ServerURL}/whapi/wagon/sellall?wagonidx=1&token=16995a9581c74b18ad1584ad9c68d245
- Return:
- 		{
 			error: {STRING},   			/* 错误 */
			wagonIdx: {INT},			/* 0:general 1:temp 2:social */
			delKeys: [INT, ...],		/* 物品的key，用来找到并删除*/
		}


## whapi/pvp/request
- Method: GET
- Desc: 请求对手信息
- Param:
-		无

- Example: 
-		{ServerURL}/whapi/pvp/request?token=16995a9581c74b18ad1584ad9c68d245

- Return: 
- 		{
 			error: {STRING},   				/* 错误 */
			bands: [						/* 三组对手band信息 */
				{
					userId:					/* 用户id */
					userName:				/* 用户名字 */
					formation: {INT}, 		/* 阵形id */
					multiplier: {FLOAT},	/* 倍率 */
					members: [
						protoId: {INT},		/* 原型id（卡片类型） */
						level: {INT},		/* 等级 */
						exp: {INT},			/* 经验值 */
						hp: {INT},			/* 总hp */
						atk: {INT},			/* 总atk */
						def: {INT},			/* 总def */
						wis: {INT},			/* 总wis */
						agi: {INT},			/* 总agi */
						skl1Id: {INT},		/* 技能1id */
						skl1Lv: {INT},		/* 技能1等级 */
						skl2Id: {INT},		/* 技能2id */
						skl2Lv: {INT},		/* 技能2等级 */
						skl3Id: {INT},		/* 技能3id */
						skl3Lv: {INT},		/* 技能3等级 */
					]
				},
				...
			]
		}

## whapi/pvp/startbattle
- Method: Post
- Desc: 选择对手，开始pvp
- Param: 无
- Post:
-		{
			foeGroupIdx: {INT},					/* 对手组索引 in (0, 1, 2) */
			band: {								/* 己方band信息 */
				formation: {INT}, 				/* 阵形id */
				members: [{INT or null}, ...]	/* 成员数组。使用cardEntityId，空位用null。注意只要求提供前排 */
			},
			allout: {BOLL}						/* 是否全力出击 */
			useItem: {INT}						/* 0：不使用 1：小号角 2：大号角 */
		}
- Example: 
-		{
			"foeGroupIdx": 1,
			"band": {
				"formation": 11,
				"members": [119, 120, null]
			},
			"allout": false,
			"useItem": 0
		}

- Return: 
- 		{
 			error: {STRING},   				/* 错误 */
		}

## whapi/pvp/submitresult
- Method: GET
- Desc: 提交pvp结果
- Param:
-		win = {BOOL}		/* 是否胜利 */

- Example: 
-		{ServerURL}/whapi/pvp/submitresult?win=true&token=16995a9581c74b18ad1584ad9c68d245

- Return: 
- 		{
 			error: {STRING},   				/* 错误 */
		}

/* 以下未实现 */

## whapi/user/set
- Method: GET
- Desc: 完成当前地图
- Input: key / value
- Example: {ServerURL}/whapi/user/set?key=XXX&value=XXX
- Return: 
- 		{
			error : {STRING}  /* 通用格式，如果为空字符串，则为正确 */
		}






