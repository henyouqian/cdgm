playerInfo = {}
$(document).ready(function(){
	getPlayerInfo();
	$("#adv").click(function(){
		clickZone()
	})
	$("#card").click(function(){
		clickCard()
	})
});

function getPlayerInfo(){
	$.getJSON('/whapi/player/getinfo', function(json){
		var err = json.error;
		if (err){
			if (err == "err_not_exist") {
				window.location.href="create_player.html";
			}
		}else{
			playerInfo = json
			playerInfoStr = JSON.stringify(json)
			$("#info").text(playerInfoStr);
			
			window.localStorage.playerInfo = playerInfoStr
			if (playerInfo.inZoneId == 0) {
				$("#adv").text("Adventure")
				$("#ipt_band_idx").removeAttr("disabled")
				$("#ipt_zone_id").removeAttr("disabled")
			} else {
				$("#adv").text("Resume")
				$("#ipt_band_idx").attr("disabled", "disabled")
				$("#ipt_zone_id").attr("disabled", "disabled")
			}

			$("#ipt_band_idx").val(json.currentBand)
			$("#ipt_zone_id").val(json.inZoneId)
		}
	});
}

function clickZone(){
	var currentBand = parseInt($("#ipt_band_idx").val())
	var zoneId = parseInt($("#ipt_zone_id").val())
	if (currentBand && zoneId) {
		var tmp = {}
		tmp.currentBand = currentBand
		tmp.zoneId = zoneId
		window.localStorage.tmp = JSON.stringify(tmp)
		window.location.href="zone.html";
	} else {
		alert("Band index or zone id error")
	}
}

function clickCard(){
	window.location.href="card.html";
}