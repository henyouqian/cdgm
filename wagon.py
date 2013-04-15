import simplejson as json
import util

WAGON_CARD_TYPE = 0

class Wagon(object):
	"""
	[type, value, time]
		if type > 0: It is item, type is item's id, value is item number
		if type ==0: It is card, value is card entity id
		time is when put into the wagon, the type is string of datetime
	"""
	def __init__(self, json_str):
		self.data = json.loads(json_str)

	def addItem(self, itemId, itemNum):
		self.data.append([itemId, itemNum, util.datetime_to_str(util.utc_now())])

	def addCard(self, cardEntityId):
		self.data.append([WAGON_CARD_TYPE, cardEntityId, util.datetime_to_str(util.utc_now())])

	def getItem(self, obj):
		if obj[0] == WAGON_CARD_TYPE:
			return None
		return {"id":obj[0], "num":obj[1], "time":util.parse_datetime(obj[2])}

	def getCard(self, obj):
		if obj[0] != WAGON_CARD_TYPE:
			return None
		return {"id":obj[1], "time":util.parse_datetime(obj[2])}