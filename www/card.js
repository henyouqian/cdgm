cards = null

$(document).ready(function(){
	$("#btn_add").click(addCard)
	$("#btn_sell").click(sellCard)
	$("#btn_evo").click(evolution)
	$("#btn_scf").click(sacrifice)

	playerInfo = JSON.parse(window.localStorage.playerInfo)
	cards = playerInfo.cards

	updateCards()
})

function saveLocalStorage() {
	window.localStorage.playerInfo = JSON.stringify(playerInfo)
}

function updateCards() {
	var ul = $("#ul_cards")
	ul.empty()
	for (var i = 0; i < cards.length; ++i) {
		card = cards[i]
		hp = card.hp + card.hpCrystal + card.hpExtra
		atk = card.atk + card.atkCrystal + card.atkExtra
		def = card.def + card.defCrystal + card.defExtra
		wis = card.wis + card.wisCrystal + card.wisExtra
		agi = card.agi + card.agiCrystal + card.agiExtra

		str = "id:" + card.id
		str += " type:" + card.protoId
		str += " level:" + card.level
		str += " exp:" + card.exp
		str += " hp:" + hp
		str += " atk:" + atk
		str += " def:" + def
		str += " wis:" + wis
		str += " agi:" + agi
		str += " skl1Id:" + card.skill1Id
		str += " skl1Lv:" + card.skill1Level
		str += " skl1Exp:" + card.skill1Exp
		if (card.skill2Id) {
			str += " skl2Id:" + card.skill2Id
			str += " skl2Lv:" + card.skill2Level
			str += " skl2Exp:" + card.skill2Exp
		}
		if (card.skill3Id) {
			str += " skl3Id:" + card.skill3Id
			str += " skl3Lv:" + card.skill3Level
			str += " skl3Exp:" + card.skill3Exp
		}

		ul.append("<li id=card_id_'"+card.id+"'>"+str+"</li>")
	}
}

function addCard() {
	proto = $("#ipt_add_type").val()
	level = $("#ipt_add_level").val()
	$.getJSON('/whapi/card/create',{"proto":proto, "level":level}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			cards.push(json.card)
			updateCards()
			saveLocalStorage()
		}
	})
}

function sellCard() {
	id = $("#ipt_sell_id").val()
	$.getJSON('/whapi/card/sell',{"id":id}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			cards = cards.filter(function(v){return v.id != json.id})
			updateCards()
			saveLocalStorage()
		}
	})
}

function evolution() {
	card1 = $("#ipt_evo1").val()
	card2 = $("#ipt_evo2").val()
	$.getJSON('/whapi/card/evolution',{"cardid1":card1, "cardid2":card2}, function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			evoCard = json.evoCard
			cards = cards.filter(function(v){return v.id != json.delCardId})
			for (var i in cards) {
				card = cards[i]
				if (card.id == evoCard.id) {
					cards[i] = evoCard
				}
				break
			}
			updateCards()
			saveLocalStorage()
		}
	})
}

function sacrifice() {
	var cards = []
	for (var i = 0; i < 9; ++i) {
		var card = $("#ipt_scf"+i).val()
		if (card) {
			n = parseInt(card)
			if (!isNaN(n))		
				cards.push(n)
		}
	}

	console.log(cards)
	
	$.post('/whapi/card/sacrifice', JSON.stringify(cards), function(json){
		var err = json.error
		if (err){
			alert(err)
		}else{
			console.log(json)
			cards = cards.filter(function(card){return json.sacrificers.indexOf(card.id) == -1})
			master = json.master
			for (var i in cards) {
				card = cards[i]
				if (card.id == master.id) {
					card.skill1Level = master.skill1Level
					card.skill1Exp = master.skill1Exp
					card.skill2Level = master.skill2Level
					card.skill2Exp = master.skill2Exp
					card.skill3Level = master.skill3Level
					card.skill3Exp = master.skill3Exp
				}
				break
			}
			updateCards()
			saveLocalStorage()
		}
	}, "json")
}

