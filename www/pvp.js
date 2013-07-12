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

	
}
