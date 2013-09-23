function Controller($scope, $http) {

	$scope.apilists = [
		{
			"tab":"auth",
			"path":"authapi",
			"apis":[
				{
					"name": "login",
					"method": "GET",
					"data": {"username":"admin", "password":"admin"}
				},
			]
		},
		{
			"tab":"store",
			"path":"whapi/store",
			"apis":[
				{
					"name": "list",
					"method": "GET",
					"data": ""
				},{
					"name": "buy",
					"method": "POST",
					"data": {"goodsId": 1, "num": 1}
				},
			]
		},
		{
			"tab":"news",
			"path":"whapi/news",
			"apis":[
				{
					"name": "list",
					"method": "GET",
					"data": ""
				},{
					"name": "read",
					"method": "POST",
					"data": {"newsId": 1}
				},
			]
		},
		{
			"tab":"instance",
			"path":"whapi/instance",
			"apis":[
				{
					"name": "list",
					"method": "GET",
					"data": ""
				},{
					"name": "zonelist",
					"method": "POST",
					"data": {"instanceID": 123}
				},{
					"name": "enterzone",
					"method": "POST",
					"data": {"zoneid": 500001, "bandidx":0}
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
	var historyCodeMirror = CodeMirror.fromTextArea(historyTextArea, 
		{
			theme: "elegant",
			readOnly: true
		}
	);
	sendCodeMirror.setSize("100%", 500)
	recvCodeMirror.setSize("100%", 500)
	historyCodeMirror.setSize("100%", 600)
	sendCodeMirror.addKeyMap({
		"Ctrl-,": function(cm) {
			var hisList = inputHistory[$scope.currUrl]
			if (isdef(hisList)) {
				var idx = Math.max(0, Math.min(hisList.length-1, inputHisIdx-1))
				if (inputHisIdx != idx) {
					inputHisIdx = idx
					sendCodeMirror.doc.setValue(hisList[inputHisIdx][0])
					recvCodeMirror.doc.setValue(hisList[inputHisIdx][1])
				}
			}
		},
		"Ctrl-.": function(cm) {
			var hisList = inputHistory[$scope.currUrl]
			if (isdef(hisList)) {
				var idx = Math.max(0, Math.min(hisList.length-1, inputHisIdx+1))
				if (inputHisIdx != idx) {
					inputHisIdx = idx
					sendCodeMirror.doc.setValue(hisList[inputHisIdx][0])
					recvCodeMirror.doc.setValue(hisList[inputHisIdx][1])
				}
			}
		},
		"Esc":function(cm) {
			var api = $scope.currApi
			if (api && api.data) {
				sendCodeMirror.doc.setValue(JSON.stringify(api.data, null, '\t'))
			} else {
				sendCodeMirror.doc.setValue("")
			}
			recvCodeMirror.doc.setValue("")
		}
	}) 

	CodeMirror.signal(sendCodeMirror, "keydown", 2)

	var inputHistory = {}
	var sendInput = ""
	var sendUrl=""
	var inputHisIdx = 0

	$scope.currApi = null

	$scope.onApiClick = function(api, path) {
		if ($scope.currApi != api) {
			$("#btn-send").removeAttr("disabled")
			$scope.currApi = api
			$scope.currUrl = path+"/"+$scope.currApi.name
			inputHisIdx = 0
			var hisList = inputHistory[$scope.currUrl]
			if (isdef(hisList)) {
				inputHisIdx = hisList.length-1
				sendCodeMirror.doc.setValue(hisList[inputHisIdx][0])
				recvCodeMirror.doc.setValue(hisList[inputHisIdx][1])
			} else {
				if (api.data) {
					sendCodeMirror.doc.setValue(JSON.stringify(api.data, null, '\t'))
				}else{
					sendCodeMirror.doc.setValue("")
				}
				recvCodeMirror.doc.setValue("")
			}
		}
		sendCodeMirror.focus()
	}

	$scope.queryTick = 0
	var lastHisText = ""
	$scope.send = function() {
		var input = sendCodeMirror.doc.getValue()
		var inputText = input
		if (input) {
			try {
				input = JSON.parse(input)
			} catch(err) {
				alert("parse json error")
				return
			}	
		}

		var onReceive = function(json) {
			printQueryTick()
			var replyText = JSON.stringify(json, null, '\t')
			recvCodeMirror.doc.setValue(replyText)

			//history
			var hisDoc = historyCodeMirror.getDoc()
			hisDoc.setCursor({line: 0, ch: 0})

			inputTextTab = "\t"+inputText.replace(/\n/g, "\n\t");
			replyTextTab = "\t"+replyText.replace(/\n/g, "\n\t");

			var hisText = "=> " + $scope.currUrl + "\n" + inputTextTab + "\n<=\n" + replyTextTab + "\n"
			hisText += "------------------------\n"
			if (lastHisText != hisText) {
				lastHisText = hisText
				hisDoc.replaceSelection(hisText, "start")

				//input history
				if (isdef(inputHistory[sendUrl])) {
					var inHisList = inputHistory[sendUrl]
					if (inHisList[inHisList.length-1] != sendInput) {
						inputHistory[sendUrl].push([sendInput, replyText])
					}
				} else {
					inputHistory[sendUrl] = [[sendInput, replyText]]
				}
				inputHisIdx = inputHistory[sendUrl].length-1
			}
			sendCodeMirror.focus()
		}

		var onFail = function(obj) {
			printQueryTick()
			var text = obj.status + ":" + obj.statusText + "\n\n" + JSON.stringify(obj.responseJSON, null, '\t')
			recvCodeMirror.doc.setValue(text)
		}

		function printQueryTick() {
			$scope.$apply(function(){
				$scope.queryTick = Math.round(window.performance.now() - t)
			});
		}

		sendInput = inputText
		sendUrl = $scope.currUrl
		var url = "/"+sendUrl
		var t = window.performance.now()
		if ($scope.currApi.method == "GET") {
			$.getJSON(url, input, onReceive)
			.fail(onFail)
		}else if ($scope.currApi.method == "POST") {
			$.post(url, sendCodeMirror.doc.getValue(), onReceive, "json")
			.fail(onFail)
		}
	}

	$('#collapseOne').on('shown.bs.collapse', function () {
		historyCodeMirror.refresh()
	})
}