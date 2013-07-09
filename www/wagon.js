gWagonIdx = 0
$(document).ready(function(){
	$("#tab_general").click(function(){listWagon(0)})
	$("#tab_temp").click(function(){listWagon(1)})
	$("#tab_social").click(function(){listWagon(2)})

	$("#btn_back").click(back)
	$("#btn_accept").click(accept)
	$("#btn_acceptall").click(acceptAll)
	$("#btn_sellall").click(sellAll)
})

function listWagon(wagonIdx)
{
	gWagonIdx = wagonIdx
	$("#wagon_items").empty()

	input = {"wagonIdx":wagonIdx, "startIdx":0, "count":20}
	$.post('/whapi/wagon/list', JSON.stringify(input), function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			var items = json.items
			js = json
			for (var i in items) {
				var item = items[i]
				$("#wagon_items").append("<li>" + item.key + "  " + JSON.stringify(item) +"</li>")
			}
			var cards = json.cards
			for (var i in cards) {
				var card = cards[i]
				$("#wagon_items").append("<li>" + card.key + "  " + JSON.stringify(card) +"</li>")

			}
		}
	}, "json")
}

function back()
{
	window.location.href="main.html"
}

function accept()
{
	var keys = $("#ipt_accept").val()
	keys = "[" + keys + "]"
	post_data ='{"keys":'+keys+'}' 
	$.post('/whapi/wagon/accept', post_data, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
			listWagon(gWagonIdx)
		}
	}, "json")
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

function sellAll()
{
	$.getJSON('/whapi/wagon/sellall', {"wagonidx":gWagonIdx}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			alert(JSON.stringify(json))
			listWagon(gWagonIdx)
		}
	})
}