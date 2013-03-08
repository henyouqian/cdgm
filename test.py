import g
import tornado.web
import brukva
import adisp
import simplejson as json

class TestRedis(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        v = [22, 1, {'xx':"fs", "4":45}]

        rv = yield g.redis.setex("usertoken", 60, json.dumps(v))
        self.write(str(rv))
        self.finish()

handlers = [
    (r"/api/test/redis", TestRedis),
]