function Controller($scope, $http) {

	$scope.getPlayerInfo = function() {
		var userName = $scope.userNameInput
		if (!userName) {
			alert("need user name")
			return
		}
		$.getJSON('/whapi/admin/getPlayerInfo', {"userName": userName}, function(json){
			var err = json.error;
			if (err){
				alert(err)
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
				alert(err)
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
				alert(err)
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
				alert(err)
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
				alert(err)
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
				alert(err)
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
				alert(err)
			}else{
				$scope.$apply(function(){
					$scope.playerInfo.money = json.money
				})
			}
		})
	}

}
