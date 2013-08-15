function Controller($scope, $http) {

	function errProc(err) {
		alert(err)
		if (err == "err_auth") {
			window.location.href="login.html?redirect=leaderboard.html"
		}
	}

	//===================================
	$scope.order = "ASC"
	function listLeaderboards() {
		$.getJSON('/whapi/leaderboard/list', function(json){
			var err = json.error;
			if (err){
				errProc(err)
			}else{
				$scope.$apply(function(){
					$scope.leaderboards = json.leaderboards
				})
			}
		})
	}
	listLeaderboards()

	//===================================
	$scope.create = function() {
		var begintime = $("#begintime").val()
		var endtime = $("#endtime").val()
		if ((!begintime) || (!endtime)) {
			alert("fill the datetime")
			return
		}
		if (begintime >= endtime) {
			alert("begintime >= endtime")
			return
		}
		var key = $scope.key
		var order = $scope.order
		if (!key) {alert("!key"); return;}
		if (!order) {alert("!order"); return;}

		$.getJSON("/whapi/leaderboard/create", {"key": key, "begintime": begintime, "endtime": endtime, "order":order}, function(json){
			var err = json.error;
			if (err){
				errProc(err)
			} else {
				$scope.$apply(function(){
					$scope.leaderboards = [json.leaderboard].concat($scope.leaderboards)
				})
			}
		})
	}

	//===================================
	$scope.view = function(key) {
		window.location.href="scores.html?key="+key
	}

}

$(function() {
	$(".form_datetime").datetimepicker({format: 'yyyy-mm-dd hh:ii:ss'});
});
