import tornado.web
import json

err_param = "err_param"
err_exist = "err_exist"
err_not_exist = "err_not_exist"
err_not_match = "err_not_match"
err_db = "err_db"
err_redis = "err_redis"

def send_error(hdl, err):
    reply = {"error":err}
    hdl.write(json.dumps(reply))
    hdl.finish()