# Asynchronous redis interface for Tornado.
#
# Author: Liwei 2013

from functools import partial

import tornado.ioloop

from threadpool import ThreadPool
from adisp import process, async
import logging
import redis

class Redis:
    def __init__(self,
                 host='localhost', port=6379, db=0,
                 ioloop=tornado.ioloop.IOLoop.instance(),
                 num_threads=10,
                 queue_timeout=1,
                 thread_idle_life=60*60):
        self._host = host
        self._port = port
        self._db = db
        
        self._threadpool = ThreadPool(
            per_thread_init_func=self.create_connection,
            per_thread_close_func=self.close_connection,
            num_threads=num_threads,
            queue_timeout=queue_timeout,
            thread_idle_life=thread_idle_life)
        self._ioloop = ioloop

    def create_connection(self):
        r = redis.StrictRedis(host=self._host, port=self._port, db=self._db)
        return r

    def close_connection(self, r):
        del r


    def stop(self):
        self._threadpool.stop()

    @async
    def exe(self, *args, **options):
        callback = options["callback"]
        del options["callback"]
        self._threadpool.add_task(
            partial(self._exec, *args, **options), callback)

    def _exec(self, *args, **options):
        r = options["thread_state"]
        del options["thread_state"]
        return r.execute_command(*args, **options)
