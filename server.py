import g
import config
import threading

import util
import auth
import player
import zone
import redistest
import card
import wagon
import pvp

from tornado import web, httpserver, ioloop, options
import brukva
from adb import Database
import logging
import os
import random
import time

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


handlers = auth.handlers + player.handlers + zone.handlers + redistest.handlers + card.handlers + wagon.handlers + pvp.handlers

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
        # c = brukva.Client(**config.redis)
        # c.connect()
        # redis_conn_life = 0
        for __ in xrange(2):
            c = brukva.Client(**config.redis)
            c.connect()
            redis_pool.append([c, time.time()+config.redis_conn_life])

        def redis():
            ct = random.choice(redis_pool)
            if (not ct[0].connection.connected()) or time.time() > ct[1]:
                # ct[0].disconnect()
                ct[0] = brukva.Client(**config.redis)
                ct[0].connect()
                ct[1] = time.time() + config.redis_conn_life
            return ct[0].async
        g.redis = redis
    except:
        print "redis connecting failed"
        raise

    # database
    g.authdb = Database(**config.auth_db)
    g.whdb = Database(**config.wh_db)

    # keep alive thread
    # thr = KeepAliveThread()
    # thr.start()

    try:
        #sync time from sql server
        util.sync_time()
        
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
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt as e:
        print "KeyboardInterrupt."
    finally:
        print "Server shutting down..."
        # thr.stop();
        g.authdb.stop()
        g.whdb.stop()
        exit(0)

if __name__ == "__main__":
    main()