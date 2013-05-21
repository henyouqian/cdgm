﻿INIT_ZONE_ID = 10101
INIT_MAX_CARD = 40
INIT_MAX_TRADE = 5
INIT_XP = 3
INIT_AP = 30
AP_ADD_DURATION = 5 #5*60
XP_ADD_DURATION = 15 #15*60

# INIT_SILVER_COIN = 2
# INIT_BRONZE_COIN = 5
INIT_GOLD = 10000
BAND_NUM = 3
__band = {"formation":1, "members":[None, None, None, None, None, None]}
INIT_BANDS = [__band.copy() for __ in xrange(BAND_NUM)]
INIT_ITEMS = {1:5, 2:10, 7:50, 8:50}	# {3:5, 5:34} => id:count		7:bronzeCoin, 8:silverCoin
INIT_WAGON = []
WARLORD_ID_BEGIN = 117

WAGON_TYPE_GENERAL = 0
WAGON_TYPE_TEMP = 1
WAGON_TYPE_SOCIAL = 2
WAGON_TEMP_DURATION = 60*60*24

MONSTER_GROUP_MEMBER_MAX = 5

MAX_PVP_BAND_NUM_PER_LEVEL = 500