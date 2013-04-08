playerInfo = null
zoneInfo = null

$(document).ready(function(){
	playerInfo = JSON.parse(window.localStorage.playerInfo)
	$("#btn_back").click(back)
	$("#btn_withdraw").click(withdraw)
	getZoneInfo()
});

function getZoneInfo() {
	if (playerInfo.isInZone) {
		$.getJSON('/whapi/zone/get', function(json){
			var err = json.error;
			if (err){
				alert(err);
			}else{
				updateZoneInfo(json)
			}
		});
	} else {
		$.getJSON('/whapi/zone/enter', {"zoneid":50101, "bandidx":0}, function(json){
			var err = json.error;
			if (err){
				alert(err);
			}else{
				updateZoneInfo(json)
			}
		});
	}
}

function back() {
	window.location.href="main.html";
}

function withdraw() {
	$.getJSON('/whapi/zone/withdraw', function(json){
		var err = json.error;
		if (err){
			alert(err);
		}else{
			window.location.href="main.html";
		}
	});
}

function updateZoneInfo(json) {
	zoneInfo = JSON.parse(JSON.stringify(json))
	var ul = $("#ul_zone")
	ul.empty()

	ul.append("<li id=li_band> zoneId:"+JSON.stringify(json.zoneId)+"</li>")
	delete json.zoneId

	ul.append("<li> startPos:("+json.startPos.x+","+json.startPos.y+")</li>")
	delete json.startPos

	ul.append("<li> goalPos:("+json.goalPos.x+","+json.goalPos.y+")</li>")
	delete json.goalPos

	ul.append("<li id=li_curr_pos> currPos:("+json.currPos.x+","+json.currPos.y+")</li>")
	delete json.currPos

	ul.append("<li id=li_red_case> redCase:"+JSON.stringify(json.redCase)+"</li>")
	delete json.redCase

	ul.append("<li id=li_gold_case> goldCase:"+JSON.stringify(json.goldCase)+"</li>")
	delete json.goldCase

	//band info
	ul.append("<li id=li_band> band:"+JSON.stringify(json.band)+"</li>")
	delete json.band
}