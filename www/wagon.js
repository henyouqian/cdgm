gWagonIdx = 0
$(document).ready(function(){
	$("#tab_general").click(function(){listWagon(0)})
	$("#tab_temp").click(function(){listWagon(1)})
	$("#tab_social").click(function(){listWagon(2)})

	$("#btn_back").click(back)
	$("#btn_accept").click(accept)
	$("#btn_acceptall").click(acceptAll)
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
				$("#wagon_items").append("<li>" + item.key + "  " + JSON.stringify(item) +"</li>")
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
	var key = $("#ipt_accept").val()
	$.getJSON('/whapi/wagon/accept', {"wagonidx":gWagonIdx, "key":key}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
			listWagon(gWagonIdx)
		}
	})
}

function acceptAll()
{
	$.getJSON('/whapi/wagon/accept', {"wagonidx":gWagonIdx}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
			listWagon(gWagonIdx)
		}
	})
}