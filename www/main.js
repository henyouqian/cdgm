$(document).ready(function(){
	getPlayerInfo();
});

function getPlayerInfo(){
	$.getJSON('/whapi/player/getinfo', function(json){
		var err = json.error;
		if (err == 0){
			$("#info").text(JSON.stringify(json));
			if (json.isInMap)
				$("#adv").text("resume");
			
		}else{
			if (err == "err_not_exist") {
				window.location.href="create_player.html";
			}
		}
	});
}