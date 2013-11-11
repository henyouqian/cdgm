﻿INIT_ZONE_ID = 10001
INIT_MAX_CARD = 40
INIT_MAX_TRADE = 5
INIT_XP = 3
INIT_AP = 30
AP_ADD_DURATION = 5*60
XP_ADD_DURATION = 15*60

# INIT_SILVER_COIN = 2
# INIT_BRONZE_COIN = 5
INIT_GOLD = 1000000
BAND_NUM = 3
INIT_CARDS = [[130, 10], [1, 1]]	#[[proto, level], ...]
INIT_BANDS = [{"formation":1, "members":[None, None, None, None, None, None]} for __ in xrange(BAND_NUM)]
# INIT_ITEMS = {1:50, 2:50, 3:50, 8:3, 10:50}	# {3:5, 5:34} => id:count		7:bronzeCoin, 8:silverCoin
INIT_ITEMS = {}
INIT_WAGON = []

WAGON_INDEX_GENERAL = 0
WAGON_INDEX_TEMP = 1
WAGON_INDEX_SOCIAL = 2
WAGON_TEMP_DURATION = 60*60*24

MONSTER_GROUP_MEMBER_MAX = 5

MAX_PVP_BAND_NUM_PER_LEVEL = 500

MONEY_BAG_SMALL_ID = 18
MONEY_BAG_BIG_ID = 19
RED_CASE_ID = 20
GOLD_CASE_ID = 21

HP_CRYSTAL_ID = 13
ATK_CRYSTAL_ID = 14
DEF_CRYSTAL_ID = 16
WIS_CRYSTAL_ID = 17
AGI_CRYSTAL_ID = 15
CRYSTAL_MAX = 10
POINT_PER_CRYSTAL = 50

WARLORD_MIN = 119
WARLORD_MAX = 126

CACHE_LIFE_SEC = 3600