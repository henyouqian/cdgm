$(document).ready(function(){
	getPlayerInfo();
});

function getPlayerInfo(){
	$.getJSON('/whapi/player/getinfo', function(json){
		var err = json.error;
		if (err==0){
			$("#info").text(JSON.stringify(json));
		}else{
			alert("getPlayerInfo. Error=" + err);
		}
	});
}