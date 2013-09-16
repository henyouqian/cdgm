function Controller($scope, $http) {
	$scope.apilists = [
		{
			"path":"auth",
			"apis":[
				{
					"name": "login",
					"method": "POST",
					"data": {"Username":"admin", "Password":"admin"}
				},
			]
		},
		{
			"path":"store",
			"apis":[
				{
					"name": "list",
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
			var apipath = "whapi/"+$scope.currApi.path+"/"
			if ($scope.currApi.path == "auth") {
				apipath = "authapi/"
			}
			$scope.currUrl = apipath+$scope.currApi.name
			if (api.data) {
				sendCodeMirror.doc.setValue(JSON.stringify(api.data, null, '\t'))
			} else {
				sendCodeMirror.doc.setValue("")
			}
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

