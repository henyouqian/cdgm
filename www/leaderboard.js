function Controller($scope, $http) {

	function errProc(err) {
		alert(err)
		if (err == "err_auth") {
			window.location.href="login.html?redirect=leaderboard.html"
		}
	}

	//===================================
	$scope.offset = 0
	$scope.limit = 50
	function listLeaderboards() {
		$.getJSON('/whapi/leaderboard/list', {"offset":$scope.offset, "limit":$scope.limit}, function(json){
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
		var order = "ASC"
		// $.getJSON("/whapi/leaderboard/create", {"begintime": begintime, "endtime": endtime, "order":}, function(json){
		// 	var err = json.error;
		// 	if (err){
		// 		errProc(err)
		// 	}else{
		// 		$scope.$apply(function(){
		// 			$scope.notification = json.text
		// 		})
		// 		alert("Notification changed.")
		// 	}
		// })
	}

}

$(function() {
	$(".form_datetime").datetimepicker({format: 'yyyy-mm-dd hh:ii:ss'});
});
