from error import *
from session import *
import util
import tornado.web
import adisp
import brukva
import simplejson as json
import csv
import logging
import os
from random import random, choice

import tornadoredis
import tornado.gen

class Redis(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # redis store
            # key = "redistest"
            # out = {"35,19": 1, "14,28": -2, "14,25": -1, "14,22": -2, "32,28": -2, "41,16": -2, "35,22": -2, "35,25": -2, "26,25": -2, "23,37": -1, "26,22": 1, "26,28": -2, "14,19": 4, "35,28": -2, "14,31": 10000, "38,16": -1, "35,16": -2, "17,37": 5, "17,19": -2, "26,31": -2, "26,34": 4, "26,37": -2}
            # rv = yield util.redis().set(key, "b"*10)
            # if not rv:
            #     send_error(self, err_redis)
            #     return;
           
            rv = yield util.redis().hget('redistest', "a")
            # rv = yield util.redis().randomkey()
            self.write(rv)

        except:
            send_internal_error(self)
        finally:
            self.finish()

class RedisSet(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @adisp.process
    def get(self):
        try:
            # redis store
            key = "redistest"
            out = {"35,19": 1, "14,28": -2, "14,25": -1, "14,22": -2, "32,28": -2, "41,16": -2, "35,22": -2, "35,25": -2, "26,25": -2, "23,37": -1, "26,22": 1, "26,28": -2, "14,19": 4, "35,28": -2, "14,31": 10000, "38,16": -1, "35,16": -2, "17,37": 5, "17,19": -2, "26,31": -2, "26,34": 4, "26,37": -2}
            rv = yield util.redis().hset(key, "a", "b"*100000)
            # if not rv:
            #     send_error(self, err_redis)
            #     return;
           
            # rv = yield util.redis().get('redistest')
            # rv = yield util.redis().randomkey()
            self.write("ok")

        except:
            send_internal_error(self)
        finally:
            self.finish()

CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=10,
                                              wait_for_available=True)

from tornado.httpclient import AsyncHTTPClient
class Redis2(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.engine
    # @tornado.gen.coroutine
    def get(self):
        try:
            c = tornadoredis.Client(connection_pool=CONNECTION_POOL)
            foo = yield tornado.gen.Task(c.hgetall, 'redistest')
            # foo = yield c.hgetall('redistest')

            # http_client = AsyncHTTPClient()
            # response = yield http_client.fetch("http://weibo.com")
            # response = yield tornado.gen.Task(http_client.fetch, "http://weibo.com")
            self.write(foo)

        except:
            send_internal_error(self)
        finally:
            self.finish()

import redis
r = redis.Redis("localhost", 6379)
class Redis3(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        try:
            foo = r.hget('redistest', 'a')
            self.write(foo)

        except:
            send_internal_error(self)
        finally:
            self.finish()

handlers = [
    (r"/whapi/redis", Redis),
    (r"/whapi/redisset", RedisSet),
    (r"/whapi/redis2", Redis2),
    (r"/whapi/redis3", Redis3),
]