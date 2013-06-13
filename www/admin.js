function Controller($scope, $http) {

	function checkAccount() {
		$.getJSON('/whapi/admin/checkAccount', function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.notification = json.notification
				});
			}
		});
	}
	checkAccount()

	function errProc(err) {
		alert(err)
		if (err == "err_auth") {
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


	$scope.submitNotification = function() {
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
	
	
}
