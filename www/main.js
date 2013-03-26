playerInfo = {}
$(document).ready(function(){
	getPlayerInfo();
	$("#adv").click(function(){
		clickZone()
	})
});

function getPlayerInfo(){
	$.getJSON('/whapi/player/getinfo', function(json){
		var err = json.error;
		if (err == 0){
			playerInfo = json
			playerInfoStr = JSON.stringify(json)
			$("#info").text(playerInfoStr);
			
			window.localStorage.playerInfo = playerInfoStr
			if (json.isInMap)
				$("#adv").text("resume");

		}else{
			if (err == "err_not_exist") {
				window.location.href="create_player.html";
			}
		}
	});
}

function clickZone(){
	window.location.href="zone.html";
}