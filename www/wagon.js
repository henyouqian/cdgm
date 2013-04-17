gWagonIdx = 0
$(document).ready(function(){
	$("#tab_general").click(function(){listWagon(0)})
	$("#tab_temp").click(function(){listWagon(1)})
	$("#tab_social").click(function(){listWagon(2)})

	$("#btn_back").click(back)
	$("#btn_accept").click(accept)
})

function listWagon(wagonIdx)
{
	gWagonIdx = wagonIdx
	$("#wagon_items").empty()

	$.getJSON('/whapi/wagon/list', {"wagonidx":wagonIdx}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			var items = json.wagons[0].items
			console.log(json)
			for (var i in items) {
				var item = items[i]
				$("#wagon_items").append("<li>" + i + ". " + JSON.stringify(item) +"</li>")
			}
			
		}
	})
}

function back()
{
	window.location.href="main.html"
}

function accept()
{
	var itemIdx = $("#ipt_accept").val()
	if (parseInt(itemIdx) == NaN) {
		alert("index must be int")
		return
	}
	$.getJSON('/whapi/wagon/accept', {"wagonidx":gWagonIdx, "itemidx":itemIdx}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			if (gWagonIdx != json.wagonIdx) {
				return
			}
			alert(JSON.stringify(json))
			listWagon(gWagonIdx)
		}
	})
}