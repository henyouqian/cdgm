function Controller($scope, $http) {

	function errProc(err) {
		alert(err)
		if (err == "err_auth") {
			window.location.href="login.html?redirect=leaderboard.html"
		}
	}

	//===================================
	$scope.key = getUrlParam("key")
	function listScores() {
		$.getJSON('/whapi/leaderboard/getranks', {"key":$scope.key, "offset":0, "limit":30}, function(json){
			var err = json.error
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.ranks = json.ranks
				})
			}
		})
	}
	listScores()
	
	$scope.back = function() {
		window.location.href="leaderboard.html"
	}

	$scope.deleteModal = function() {
		$('#myModal').modal({"backdrop":"static"})
		// window.location.href="leaderboard.html"
	}

	$scope.del = function() {
		$.getJSON('/whapi/leaderboard/delete', {"key":$scope.key}, function(json){
			var err = json.error
			if (err){
				errProc(err)
			}else{
				window.location.href="leaderboard.html"
			}
		})
		
	}
}
