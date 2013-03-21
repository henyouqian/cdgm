import auth
import player
import zone
import g
import config
import threading

from tornado import web, httpserver, ioloop
from tornado import options
import brukva
from adb import Database
import logging
import os
import random

class KeepRedisAliveTread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(KeepRedisAliveTread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        while True:
            g.redis.exists("a")
            self._stop.wait(30)
            if self._stop.is_set():
                break


handlers = auth.handlers + player.handlers + zone.handlers
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
        g.redis = c.async
    except:
        print "redis connecting failed"
        return

    # database
    g.authdb = Database(**config.auth_db)
    g.whdb = Database(**config.wh_db)
    
    # application
    application = web.Application(
        handlers,
        debug = config.debug,
        cookie_secret=config.cookie_secret
    )
    application.listen(params.port)
    if (config.debug):
        logging.getLogger().setLevel(logging.DEBUG)
        options.enable_pretty_logging()
        print "Server running in debug mode"
    else:
        logging.disable(logging.WARNING)
        print "Server running"

    # keep redis alive thread
    thr = KeepRedisAliveTread()
    thr.start()

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