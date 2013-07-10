function Controller($scope, $http) {

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
		$.getJSON('/whapi/pvp/createtestdata', function(json){
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
