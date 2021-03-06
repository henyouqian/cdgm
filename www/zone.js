playerInfo = null
zoneInfo = null
zoneId = 1

$(document).ready(function(){
	playerInfo = JSON.parse(window.localStorage.playerInfo)
	$("#btn_back").click(back)
	$("#btn_withdraw").click(withdraw)
	$("#btn_move").click(move)
	$("#btn_complete").click(complete)
	$("#btn_teleport").click(teleport)
	$("#btn_redgold").click(redGold)
	getZoneInfo()
})

function updateZoneInfo() {
	var ul = $("#ul_zone")
	ul.empty()

	var zone = JSON.parse(JSON.stringify(zoneInfo))
	var player = JSON.parse(JSON.stringify(playerInfo))

	ul.append("<li id=li_band> zoneId:"+JSON.stringify(zone.zoneId)+"</li>")
	ul.append("<li> startPos:("+zone.startPos.x+","+zone.startPos.y+")</li>")
	ul.append("<li> goalPos:("+zone.goalPos.x+","+zone.goalPos.y+")</li>")
	ul.append("<li id=li_curr_pos> currPos:("+zone.currPos.x+","+zone.currPos.y+")</li>")
	ul.append("<li id=li_red_case> redCase:"+JSON.stringify(zone.redCase)+"</li>")
	ul.append("<li id=li_gold_case> goldCase:"+JSON.stringify(zone.goldCase)+"</li>")
	ul.append("<li id=li_band> band:"+JSON.stringify(zone.band)+"</li>")

	ul.append("<li> ap:"+JSON.stringify(player.ap)+"</li>")
	ul.append("<li> money:"+JSON.stringify(player.money)+"</li>")
	ul.append("<li> objs:"+JSON.stringify(zone.objs.sort())+"</li>")

	if ((zone.currPos.x == zone.goalPos.x) && (zone.currPos.y == zone.goalPos.y)) {
		$("#btn_complete").removeAttr("disabled")
	} else {
		$("#btn_complete").attr("disabled", 1)
	}
}

function getZoneInfo() {
	if (playerInfo.inZoneId) {
		$.getJSON('/whapi/zone/get', function(json){
			var err = json.error
			if (err){
				alert(err)
				window.location.href="main.html"
			}else{
				zoneInfo = JSON.parse(JSON.stringify(json))
				updateZoneInfo()
			}
		})
	} else {
		tmp = JSON.parse(window.localStorage.tmp)
		$.getJSON('/whapi/zone/enter', {"zoneid":tmp.zoneId, "bandidx":tmp.currentBand}, function(json){
			var err = json.error
			if (err){
				alert(err)
				window.location.href="main.html"
			}else{
				zoneInfo = JSON.parse(JSON.stringify(json))
				updateZoneInfo()
			}
		})
	}
}

function back() {
	window.location.href="main.html"
}

function withdraw() {
	$.getJSON('/whapi/zone/withdraw', function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			window.location.href="main.html"
		}
	})
}

function move() {
	var stepNum = parseInt($("#ipt_move").val())+1
	var currPos = zoneInfo.currPos
	var goalPos = zoneInfo.goalPos
	var steps = []
	for (var i = 0; i < stepNum; ++i) {
		var step = [currPos.x, currPos.y-i*3]
		steps.push(step)
	}
	if (steps.length == 0) {
		alert("already got goal")
		return
	}

	$.post('/whapi/zone/move', JSON.stringify(steps), function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			console.log(json)

			playerInfo.ap = json.ap
			var str = "ap:" + json.ap + "\n"

			zoneInfo.currPos = json.currPos
			str += "currPos:(" + json.currPos.x + "," + json.currPos.y + ")\n"

			if (json.moneyAdd) {
				playerInfo.money += json.moneyAdd
				str += "moneyAdd:" + json.moneyAdd + "\n"
			}
			if (json.redCaseAdd) {
				zoneInfo.redCase += json.redCaseAdd
				str += "redCaseAdd:" + json.redCaseAdd + "\n"
			}
			if (json.goldCaseAdd) {
				zoneInfo.goldCase += json.goldCaseAdd
				str += "goldCaseAdd:" + json.goldCaseAdd + "\n"
			}
			var battle = false
			if (json.monGrpId) {
				str += "Battle:" + json.monGrpId + "\n"
				battle = true
			}

			if (json.items.length) {
				str += "GotItems:" + JSON.stringify(json.items) + "\n"
			}

			if (json.complete) {
				
			}

			alert(str)
			updateZoneInfo()

			//send battle result
			if (battle) {
				var members = copyObj(zoneInfo.band.members)
				members = members.slice(0, members.length/2)
				for (idx in members) {
					if (members[idx]) {
						var hp = members[idx].hp - 100;
						hp = Math.max(0, hp)
						members[idx].hp = hp
					}
				}

				var battleResult = {}
				battleResult["isWin"] = true
				battleResult["members"] = members
				$.post('/whapi/zone/battleresult', JSON.stringify(battleResult), function(json){
					if (json.error) {
						alert(json.error)
					} else {
						console.log(json)
						zoneInfo.currPos = json.currPos
						updateZoneInfo()
					}
				}, "json")
			}
		}
	}, "json")
}

function complete() {
	$.getJSON('/whapi/zone/complete', function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
		}
		window.location.href="main.html"
	})
}

function teleport() {
	var x = parseInt($("#ipt_teleport_x").val())
	var y = parseInt($("#ipt_teleport_y").val())
	if (!x || !y) {
		alert("x or y must be number")
		return
	}
	$.getJSON('/whapi/cheat/teleport',{"x":x, "y":y}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
			zoneInfo.currPos = {"x":json.x, "y":json.y}
			updateZoneInfo()
		}
	})
}


function redGold() {
	var red = parseInt($("#ipt_red_num").val())
	var gold = parseInt($("#ipt_gold_num").val())
	if (!red || !gold) {
		alert("red or gold must be number")
		return
	}
	$.getJSON('/whapi/cheat/redGold',{"red":red, "gold":gold}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
			zoneInfo.redCase = json.red
			zoneInfo.goldCase = json.gold
			updateZoneInfo()
		}
	})
}


