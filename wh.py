#! ./env/bin/python

import config

import util
import auth
import player
import zone
import card
import wagon
import pvp
import experiment
import cheat
import admin
import version

from tornado import web, httpserver, ioloop
import logging
import random
import traceback
import os


handlers = auth.handlers + player.handlers + zone.handlers + card.handlers \
            + wagon.handlers + pvp.handlers + experiment.handlers \
            + cheat.handlers + admin.handlers + version.handlers

if config.debug:
    import cheat
    handlers = handlers + cheat.handlers

def main(port=8888):
    random.seed()

    try:
        util.init_redis()
        util.init_db()
    
        #sync time from sql server
        util.sync_time()
        
        # application
        application = web.Application(
            handlers,
            debug = config.debug,
            cookie_secret=config.cookie_secret
        )
        application.listen(port)

        util.init_logger(config.debug)
        logging.info("Server starting")
        if (config.debug):
            logging.info("Debug mode")

        # server loop
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info("Process pid=%d exiting.", os.getpid())
    except Exception as e:
        logging.error(e)
        logging.error(traceback.format_exc())
        raise e
    finally:
        logging.info("Server shutting down...")
        util.stop_db()
        exit(0)


def handler(signum, frame):
    raise KeyboardInterrupt

import signal
signal.signal(signal.SIGINT, handler)

if __name__ == "__main__":
    main()