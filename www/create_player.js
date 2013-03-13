$(document).ready(function(){
	// getPlayerInfo();
	$(".thumbnails>li>a").click(function(){
		selectPlayer(this.id)
	});
});

function selectPlayer(id){
	$.getJSON('/whapi/player/create', {warlord:id}, function(json){
		var err = json.error;
		if (err==0){
			window.location.href="main.html";
		}else{
			alert("selectPlayer. Error=" + err);
		}
	});
}