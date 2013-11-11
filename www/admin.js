function Controller($scope, $http) {

	$scope.expMultiEvents = [
		{multiplier:3.4, time:"today"},
		{multiplier:4.4, time:"tomorrow"}
	]

	$(".form_datetime").datetimepicker({format: 'yyyy-mm-dd hh:ii:ss', todayBtn: true});

	function checkAccount() {
		$.getJSON('/whapi/admin/checkAccount', function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.notification = json.notification
					$scope.expMultiplier = json.expMultiplier
				});
			}
		});
	}
	// checkAccount()

	function getAdminInfo() {
		$.getJSON('/goapi/admin/getinfo', function(json){
			var err = json.Error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.gameEventStartTime = json.GameEvent.StartTime
					$scope.gameEventEndTime = json.GameEvent.EndTime
					$scope.gameEventType = json.GameEvent.EvtType
					$scope.gameEventNewsId = json.GameEvent.NewsId
				});
			}
		});
	}
	getAdminInfo()

	$scope.setGameEvent = function() {
		var data = JSON.stringify({
			"EvtType": parseInt($scope.gameEventType),
			"NewsId": parseInt($scope.gameEventNewsId),
			"StartTime": $("#idGameEventStartTime").val(),
			"EndTime": $("#idGameEventEndTime").val()
		})
		$.post('/goapi/gameevent/set', 
			data,
			function(json){
				if (json.Error) {
					errProc(err)
				} else {
					alert(json)
				}
			}
		)
	}

	$scope.clearLeaderboard = function() {
		if(confirm("Clear Leaderboard?")) {
			$.post('/goapi/gameevent/clearleaderboard', 
				function(json){
					if (json.Error) {
						errProc(err)
					} else {
						alert(json)
					}
				}
			)
		}
	}

	$scope.sendReward = function() {
		if(confirm("Send reward?")) {
			$.post('/goapi/gameevent/sendrewards', 
				function(json){
					if (json.Error) {
						errProc(err)
					} else {
						alert(json)
					}
				}
			)
		}
	}

	// items
	$scope.items = [
		{"id":1, "name":"邪惡葫蘆", "commet":"回復全部體力值"},
		{"id":2, "name":"治療草藥", "commet":"回復全部HP"},
		{"id":3, "name":"復活聖水", "commet":"復活一名隊員"},
		{"id":4, "name":"高級治療草藥", "commet":"回復全體隊員"},
		{"id":5, "name":"高級誘惑粉末", "commet":"100%抓取打到的怪物"},
		{"id":6, "name":"誘惑粉末", "commet":"一定幾率抓取"},
		{"id":7, "name":"初級魔石", "commet":"抽怪物"},
		{"id":8, "name":"中級魔石", "commet":"抽怪物"},
		{"id":9, "name":"高級魔石", "commet":"抽怪物"},
		{"id":10, "name":"小海螺", "commet":"回復一點戰力"},
		{"id":11, "name":"海螺號角", "commet":"回滿戰力"},
		{"id":12, "name":"任務幣", "commet":"抽怪物"},
		{"id":13, "name":"HP水晶", "commet":"增加50點HP"},
		{"id":14, "name":"ATK水晶", "commet":"增加50點ATK"},
		{"id":15, "name":"AGI水晶", "commet":"增加50點AGI"},
		{"id":16, "name":"DEF水晶", "commet":"增加50點DEF"},
		{"id":17, "name":"WIS水晶", "commet":"增加50點WIS"},
	]

	function errProc(err) {
		alert(err)
		if (err == "err_auth" || err == "err_permission") {
			window.location.href="login.html?redirect=admin.html"
		}
	}

	$scope.getPlayerInfo = function() {
		var userName = $scope.userNameInput
		if (!userName) {
			alert("need user name")
			return
		}
		$.getJSON('/whapi/admin/getPlayerInfo', {"userName": userName}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo = json.playerInfo
					$scope.cards = json.cards
				});
			}
		});
	}

	$scope.setItem = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}
		var itemId = $scope.itemIdInput
		var itemNum = $scope.itemNumInput

		if (!itemId || !itemNum) {
			alert("need itemId and itemNum")
			return
		}
		$.getJSON('/whapi/admin/setItemNum', {"userId": userId, "itemId": itemId, "itemNum": itemNum}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					var change = json.change
					alert("set item num succeed:\n"+change.id+": ("+change.from+"->"+change.to+")")
					$scope.playerInfo.items = json.items
				})
			}
		})
	}

	$scope.addItemToWagon = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}
		var itemId = $scope.itemIdInput
		var itemNum = $scope.itemNumInput

		if (!itemId || !itemNum) {
			alert("need itemId and itemNum")
			return
		}
		$.getJSON('/whapi/admin/addItemToWagon', {"userId": userId, "itemId": itemId, "itemNum": itemNum}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				alert("add item to wagon succeed:\n")
			}
		})
	}

	$scope.setLastZoneId = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		var lastZoneId = $scope.lastZoneId

		if (!lastZoneId) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setLastZoneId', {"userId": userId, "lastZoneId": lastZoneId}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.lastZoneId = json.lastZoneId
				})
			}
		})
	}

	$scope.setMaxCardNum = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		var maxCardNum = $scope.maxCardNum

		if (!maxCardNum) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setMaxCardNum', {"userId": userId, "maxCardNum": maxCardNum}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.maxCardNum = json.maxCardNum
				})
			}
		})
	}

	$scope.setMaxTradeNum = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		if (!$scope.maxTradeNum) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setMaxTradeNum', {"userId": userId, "maxTradeNum": $scope.maxTradeNum}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.maxTradeNum = json.maxTradeNum
				})
			}
		})
	}

	$scope.setLastFormation = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		if (!$scope.lastFormation) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setLastFormation', {"userId": userId, "lastFormation": $scope.lastFormation}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.lastFormation = json.lastFormation
				})
			}
		})
	}

	$scope.setMoney = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		if (!$scope.money) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setMoney', {"userId": userId, "money": $scope.money}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.money = json.money
				})
			}
		})
	}

	$scope.setAp = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		if (!$scope.ap && (!$scope.maxAp)) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setAp', {"userId": userId, "ap": $scope.ap, "maxAp": $scope.maxAp}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.ap = json.ap
					$scope.playerInfo.maxAp = json.maxAp
				})
			}
		})
	}

	$scope.setXp = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		if (!$scope.xp && (!$scope.maxXp)) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setXp', {"userId": userId, "xp": $scope.xp, "maxXp": $scope.maxXp}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.xp = json.xp
					$scope.playerInfo.maxXp = json.maxXp
				})
			}
		})
	}

	$scope.setWhcoin = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		if (!$scope.whcoin) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setWhcoin', {"userId": userId, "whcoin": $scope.whcoin}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.whcoin = json.whcoin
				})
			}
		})
	}

	$scope.addCard = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		var cardId = $scope.addCardProto
		var cardLevel = $scope.addCardLevel
		if ((!cardId) && (!cardLevel)) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/addCard', {"userId": userId, "protoId": cardId, "level": cardLevel}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.cards.push(json.card)
				})
			}
		})
	}

	$scope.addCardToWagon = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		var cardId = $scope.addCardProto
		var cardLevel = $scope.addCardLevel
		if ((!cardId) && (!cardLevel)) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/addCardToWagon', {"userId": userId, "protoId": cardId, "level": cardLevel}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				alert("addCardToWagon succeed: \n" + json.card.name)
			}
		})
	}

	$scope.setCardLevel = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		var cardId = $scope.setCardLevelId
		var cardLevel = $scope.setCardLevelLevel
		if ((!cardId) && (!cardLevel)) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setCardLevel', {"userId": userId, "cardId": cardId, "level": cardLevel}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					for (var i = 0; i < $scope.cards.length; ++i) {
						if ($scope.cards[i].id == json.cardId) {
							$scope.cards[i].level = json.level
							break;
						}
					}
				})
			}
		})
	}

	$scope.setCardSkill = function() {
		try {
			var userId = $scope.playerInfo.userId
		} catch(err) {
			alert("select user first")
			return
		}

		var cardId = $scope.setCardSkillId
		var level = $scope.setCardSkillLevel
		var index = $scope.setCardSkillIndex
		if ((!cardId) && (!level) && (!index)) {
			alert("fill the blank")
			return
		}
		$.getJSON('/whapi/admin/setCardSkillLevel', {"userId": userId, "cardId": cardId, "index": index, "level": level}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				alert("Set skill level succeed")
				$scope.$apply(function(){
					for (var i = 0; i < $scope.cards.length; ++i) {
						if ($scope.cards[i].id == json.cardId) {
							$scope.cards[i]["skill"+json.index+"Level"] = json.level
							break;
						}
					}
				})
			}
		})
	}


	$scope.setNotification = function() {
		var notification = $scope.notification
		if (!notification) {
			alert("fill the blank")
			return
		}
		$.getJSON("/whapi/admin/setNotification", {"text": notification}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.notification = json.text
				})
				alert("Notification changed.")
			}
		})
	}


	$scope.setExpMultiplier = function() {
		var expMulti = $scope.expMultiplierInput
		if (!expMulti) {
			alert("fill the blank")
			return
		}
		$.getJSON("/whapi/admin/setExpMultiplier", {"multiplier": expMulti}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.expMultiplier = json.multiplier
				})
				alert("Exp multiplier changed.")
			}
		})
	}
	
	
}
