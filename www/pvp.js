function Controller($scope, $http) {

	function getFormula() {
		$.getJSON('/whapi/pvp/getformula', function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.formula = json.formula
				})
			}
		})
	}
	getFormula()

	function getPvpRanks() {
		$.getJSON('/whapi/pvp/getranks', function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.ranks = json.ranks
				})
			}
		})
	}
	getPvpRanks()

	function errProc(err) {
		alert(err)
		if (err == "err_auth") {
			window.location.href="login.html?redirect=pvp.html"
		}
	}

	$scope.createTestData = function() {
		var priceSkillMul = $scope.formula.priceSkillMul
		if (!priceSkillMul) {
			alert("need priceSkillMul")
			return
		}
		$.getJSON('/whapi/pvp/createtestdata', {"priceSkillMul": priceSkillMul}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					getPvpRanks()
					alert("ok")
				});
			}
		});
	}

	$scope.pvpMatch = function() {
		cards = []
		if ($scope.card1)
			cards.push(parseInt($scope.card1))
		if ($scope.card2)
			cards.push(parseInt($scope.card2))
		if ($scope.card3)
			cards.push(parseInt($scope.card3))
		if ($scope.card4)
			cards.push(parseInt($scope.card4))
		if ($scope.card5)
			cards.push(parseInt($scope.card5))

		if (cards.length == 0) {
			alert("empty cards!")
			return
		}
		if (!$scope.matchNo) {
			alert("empty matchNo!")
			return
		}

		var post_data = {"cards":cards, "matchNo":parseInt($scope.matchNo)}
		post_data = JSON.stringify(post_data)

		$.post('/whapi/pvp/match', post_data, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.matchedBands = json
				})
			}
		}, "json")
	}
	
	
}
