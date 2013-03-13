import tornado.web
import json
import traceback

err_internal = "err_internal"
err_param = "err_param"
err_exist = "err_exist"
err_not_exist = "err_not_exist"
err_not_match = "err_not_match"
err_db = "err_db"
err_redis = "err_redis"
err_auth = "err_auth"

def send_error(hdl, err):
    reply = '{"error":"' + err + '"}'
    hdl.write(reply)

def send_internal_error(hdl):
	reply = '{"error":"err_internal"}'
	hdl.write(reply)
	traceback.print_exc()