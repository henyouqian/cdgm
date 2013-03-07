$(document).ready(function(){
	$('#btn_login').click(function() {
		login();
	});
	$(".input-block-level").keypress(function(event) {
		if ( event.which == 13 ) {
			login();
		}
	});
	var username = getUrlParam("username");
	if (username) {
		$("#username").val(username);
	}
});

function login(){
	var username=$('#username').val();
	var password=$('#password').val();
	if ( username == "" || password == "" ) {
		alert("Form incomplete.")
		return;
	}
	$.getJSON('/cdgmapi/auth/login', {username:username, password:password}, function(json){
		var err = json.error;
		if (err==0){
			window.location.href="main.html";
		}else{
			alert("Sign in failed. Error=" + err);
		}
	});
}