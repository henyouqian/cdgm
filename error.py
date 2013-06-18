import tornado.web
import json
import traceback
import config
import logging
import sys

err_internal = "err_internal"
err_param = "err_param"
err_post = "err_post"
err_exist = "err_exist"
err_not_exist = "err_not_exist"
err_not_match = "err_not_match"
err_db = "err_db"
err_redis = "err_redis"
err_auth = "err_auth"
err_key = "err_key"
err_value = "err_value"
err_index = "err_index"
err_permission = "err_permission"

no_error = ""

if config.debug:
    def send_error(hdl, err, text=None):
        try:
            if text:
                raise Exception(str(text))
        except:
            pass
        finally:
            reply = {"error":"%s" % err, "traceback":"%s" % traceback.format_exc()}
            hdl.write(json.dumps(reply))
            traceback.print_exc()
else:
    def send_error(hdl, err, text=None):
        reply = '{"error":"%s"}' % (err, )
        hdl.write(reply)

        if hdl.request.body:
            logging.error(self.request.body)

def send_ok(hdl):
    hdl.write('{"error":""}')

if config.debug:
    def send_internal_error(hdl):
        exc_type, exc_value, exc_traceback = sys.exc_info()
        reply = {"error":"err_internal:%s,%s"%(exc_type, exc_value), "traceback":"%s" % traceback.format_exc()}
        hdl.write(json.dumps(reply))
        traceback.print_exc()
else:
    def send_internal_error(hdl):
        reply = '{"error":"err_internal"}'
        hdl.write(reply)