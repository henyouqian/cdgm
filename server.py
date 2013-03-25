import g
import config
import threading

import auth
import player
import zone
import redistest

from tornado import web, httpserver, ioloop
from tornado import options
import brukva
from adb import Database
import logging
import os
import random

redis_pool = []

class KeepAliveThread(threading.Thread):
    def __init__(self):
        super(KeepAliveThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        while True:
            for c in redis_pool:
                c.exists("a")

            self._stop.wait(60)
            if self._stop.is_set():
                break


handlers = auth.handlers + player.handlers + zone.handlers + redistest.handlers
if config.debug:
    import cheat
    handlers = handlers + cheat.handlers

def main():
    print "Server starting..."
    random.seed()

    # command line
    options.define("port", default=8888, help="Port")
    options.parse_command_line()
    params = options.options

    # redis
    try:
        c = brukva.Client(**config.redis)
        c.connect()
        for __ in xrange(10):
            c = brukva.Client(**config.redis)
            # c.connect()
            redis_pool.append(c)

        def redis():
            c = random.sample(redis_pool, 1)[0]
            if not c.connection.connected():
                print("reconnect redis")
                c.connection.connect()
            return c.async
        g.redis = redis
    except:
        print "redis connecting failed"
        return

    # database
    g.authdb = Database(**config.auth_db)
    g.whdb = Database(**config.wh_db)

    # keep alive thread
    thr = KeepAliveThread()
    thr.start()
    
    # application
    application = web.Application(
        handlers,
        debug = config.debug,
        cookie_secret=config.cookie_secret
    )
    application.listen(params.port)
    if (config.debug):
        logging.getLogger().setLevel(logging.DEBUG)
        # options.enable_pretty_logging()
        print "Server running in debug mode"
    else:
        logging.disable(logging.WARNING)
        print "Server running"

    # server loop
    try:
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt as e:
        print "KeyboardInterrupt."
    except Exception:
        print e
    finally:
        print "Server shutting down..."
        thr.stop();
        g.authdb.stop()
        g.whdb.stop()

if __name__ == "__main__":
    main()