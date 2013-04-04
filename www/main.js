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
			if (json.isInMap)
				$("#adv").text("resume");
		}
	});
}

function clickZone(){
	window.location.href="zone.html";
}

function clickCard(){
	window.location.href="card.html";
}