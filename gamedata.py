﻿INIT_ZONE_ID = 1
INIT_MAX_CARD = 40
INIT_XP = 30
INIT_AP = 3
# INIT_SILVER_COIN = 2
# INIT_BRONZE_COIN = 5
INIT_GOLD = 10000
BAND_NUM = 3
__band = {"formation":1, "members":[None, None, None, None, None, None]}
INIT_BANDS = [__band.copy() for __ in xrange(BAND_NUM)]
INIT_ITEMS = {1:5, 2:10, 7:50, 8:50}	# {3:5, 5:34} => id:count		7:bronzeCoin, 8:silverCoin
INIT_WAGON = []
WARLORD_ID_BEGIN = 117