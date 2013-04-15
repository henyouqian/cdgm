playerInfo = {}
$(document).ready(function()
{
	getPlayerInfo();
	$("#adv").click(function(){
		clickZone()
	})
	$("#card").click(function(){
		clickCard()
	})
	$("#btn_set_band").click(function(){
		setBand()
	})
});

function getPlayerInfo()
{
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

		//band
		var div_band = $("#div_band")
		div_band.empty()
		for (var i in json.bands) {
			var band = json.bands[i]
			div_band.append('<input id="ipt_band'+i+'" class="ipt_band" type="text" style="width:450px;margin-bottom:0px" placeholder="band data"></input><br>')
			$("#ipt_band"+i).val(JSON.stringify(band))

		}
	});
}

function clickZone()
{
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

function clickCard()
{
	window.location.href="card.html";
}

function setBand()
{
	var bands = $(".ipt_band")
	var len = bands.length
	post = []
	for (var i = 0; i < len; ++i){
		var band = $(bands[i])
		post.push(band.val())
	}
	post = post.join(",")
	post = "[" + post + "]"
	
	$.post('/whapi/player/setband', post, function(json){
		var err = json.error
		if (err){
			alert(err)
			console.log(json.traceback)
		}else{
			console.log(json)
		}
	}, "json")
}