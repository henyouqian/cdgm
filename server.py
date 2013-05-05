import config

import util
import auth
import player
import zone
import card
import wagon
import pvp

from tornado import web, httpserver, ioloop, options
import logging
import random


handlers = auth.handlers + player.handlers + zone.handlers + card.handlers + wagon.handlers + pvp.handlers

if config.debug:
    import cheat
    handlers = handlers + cheat.handlers

def main():
    random.seed()

    # command line
    options.define("port", default=8888, help="Port")
    options.parse_command_line()
    params = options.options

    try:
        # redis
        util.init_redis()

        # database
        util.init_db()
    
        #sync time from sql server
        util.sync_time()
        
        # application
        application = web.Application(
            handlers,
            debug = config.debug,
            cookie_secret=config.cookie_secret
        )
        application.listen(params.port)

        util.init_logger(config.debug)
        logging.info("Server starting")
        if (config.debug):
            logging.info("Debug mode")

        # server loop
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt as e:
        logging.info("KeyboardInterrupt.")
    except Exception as e:
        logging.error(e)
        raise e
    finally:
        logging.info("Server shutting down...")
        util.stop_db()
        exit(0)

if __name__ == "__main__":
    main()