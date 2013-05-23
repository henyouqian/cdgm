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
	$.getJSON('https://'+window.location.hostname+'/authapi/login?callback=?', {"username":username, "password":password}, function(json){
		var err = json.error;
		if (err){
			alert("Sign in failed. Error=" + err);
		}else{
			window.location.href="main.html";
		}
	});
}