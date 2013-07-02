function Controller($scope, $http) {
	function getPvpSettings() {
		$.getJSON('/whapi/pvp/getsettings', function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.priceRarityMul = json.priceRarityMul
				})
			}
		})
	}
	getPvpSettings()

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
		if (!$scope.priceRarityMul) {
			alert("need priceRarityMul")
			return
		}
		$.getJSON('/whapi/pvp/createtestdata', {"priceraritymul": $scope.priceRarityMul}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					alert("ok")
				});
			}
		});
	}

	
}
