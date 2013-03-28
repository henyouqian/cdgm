$(document).ready(function(){
	$('#btn_register').click(function() {
		register();
	});
	$(".input-block-level").keypress(function(event) {
		if ( event.which == 13 ) {
			register();
		}
	});
});

function register(){
	var username = $('#username').val();
	var password = $('#password').val();
	var password2 = $('#password2').val();
	if (!username || !password || !password2) {
		alert("Form incomplete.");
		return;
	}
	if (password != password2) {
		alert("Password mismatch.");
		return;
	}
	$.getJSON('/authapi/register', {username:username, password:password}, function(json){
		var err = json.error;
		if (err){
			alert("Sign up failed. Error=" + err);
		}else{
			window.location.href="create_player.html";
		}
	});
}