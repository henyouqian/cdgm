function Controller($scope, $http) {
	$scope.apilists = [
		{
			"path":"bench",
			"apis":[
				{
					"name": "login",
					"method": "GET",
					"data": ""
				},{
					"name": "hello",
					"method": "GET",
					"data": ""
				},{
					"name": "dbsingleselect",
					"method": "GET",
					"data": ""
				},{
					"name": "dbinsert",
					"method": "GET",
					"data": ""
				},{
					"name": "dbinserttx",
					"method": "GET",
					"data": ""
				},{
					"name": "redisget",
					"method": "GET",
					"data": ""
				},{
					"name": "json",
					"method": "GET",
					"data": ""
				},
				{
					"name": "json2",
					"method": "GET",
					"data": ""
				},

			]
		},
		{
			"path":"auth",
			"apis":[
				{
					"name": "login",
					"method": "POST",
					"data": {"Username":"admin", "Password":"admin", "Appsecret":"app_secret_here"}
				},{
					"name": "logout",
					"method": "POST",
					"data": ""
				},{
					"name": "info",
					"method": "POST",
					"data": ""
				},{
					"name": "register",
					"method": "POST",
					"data": {"Username":"?", "Password":"?"}
				},{
					"name": "newapp",
					"method": "POST",
					"data": {"Name":"?"}
				},{
					"name": "listapp",
					"method": "POST",
					"data": ""
				},
			] 
		},
		{
			"path":"game",
			"apis":[
				{
					"name": "list",
					"method": "POST",
					"data": ""
				},{
					"name": "new",
					"method": "POST",
					"data": {"Id":1, "Name":"aa", "Sort":"DESC"}
				},{
					"name": "del",
					"method": "POST",
					"data": [1]
				},
			] 
		},
		{
			"path":"match",
			"apis":[
				{
					"name": "list",
					"method": "POST",
					"data": ""
				},{
					"name": "new",
					"method": "POST",
					"data": {"Name":"aa", "Gameid":1, "Begin":"2006-01-02 15:04:05", "End":"2014-01-02 15:04:05"}
				},{
					"name": "del",
					"method": "POST",
					"data": [1]
				},{
					"name": "start",
					"method": "POST",
					"data": {"MatchId":1}
				},{
					"name": "addscore",
					"method": "POST",
					"data": {"TrySecret":"xxxyyyzzz", "Score":12345}
				},
			] 
		},
		{
			"path":"matchold",
			"apis":[
				{
					"name": "new",
					"method": "POST",
					"data": {"Name":"aa", "Gameid":1, "Begin":"2006-01-02 15:04:05", "End":"2006-01-02 15:04:05", "Sort":0}
				},{
					"name": "listopening",
					"method": "POST",
					"data": ""
				},{
					"name": "listcomming",
					"method": "POST",
					"data": ""
				},{
					"name": "listclosed",
					"method": "POST",
					"data": ""
				},
			] 
		},
	]

	var sendCodeMirror = CodeMirror.fromTextArea(sendTextArea, 
		{
			theme: "elegant",
		}
	);
	var recvCodeMirror = CodeMirror.fromTextArea(recvTextArea, 
		{
			theme: "elegant",
		}
	);

	$scope.selectedApiPath = ""
	$scope.currApi = null

	$scope.onApiClick = function(api, path) {
		if ($scope.currApi != api) {
			$("#btn-send").removeAttr("disabled")
			$scope.currApi = api
			$scope.currApi.path = path
			$scope.currUrl = $scope.currApi.path+"/"+$scope.currApi.name
			if (api.data) {
				sendCodeMirror.doc.setValue(JSON.stringify(api.data, null, '\t'))
			} else {
				sendCodeMirror.doc.setValue("")
			}
			
			// recvCodeMirror.doc.setValue("")
		}
	}

	$scope.queryTick = 0

	$scope.send = function() {
		var url = "../"+$scope.currUrl
		var input = sendCodeMirror.doc.getValue()
		if (input) {
			try {
				input = JSON.parse(input)
			} catch(err) {
				alert("parse json error")
				return
			}	
		}
		var t = window.performance.now()
		function printQueryTick() {
			$scope.$apply(function(){
				$scope.queryTick = Math.round(window.performance.now() - t)
			});
		}
		if ($scope.currApi.method == "GET") {
			$.getJSON(url, input, function(json){
				printQueryTick()
				recvCodeMirror.doc.setValue(JSON.stringify(json, null, '\t'))
			})
			.fail(function(obj) {
				printQueryTick()
				var text = obj.status + ":" + obj.statusText + "\n\n" + JSON.stringify(obj.responseJSON, null, '\t')
				recvCodeMirror.doc.setValue(text) 
			})
		}else if ($scope.currApi.method == "POST") {
			$.post(url, sendCodeMirror.doc.getValue(), function(json){
				printQueryTick()
				recvCodeMirror.doc.setValue(JSON.stringify(json, null, '\t'))
			}, "json")
			.fail(function(obj) {
				printQueryTick()
				var text = obj.status + ":" + obj.statusText + "\n\n" + JSON.stringify(obj.responseJSON, null, '\t')
				recvCodeMirror.doc.setValue(text) 
			})
		}
	}

	
}

