import config

import util
import auth
import player
import zone
import redistest
import card
import wagon
import pvp

from tornado import web, httpserver, ioloop, options
import logging
import random


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
        util.stop_db()
        exit(0)

if __name__ == "__main__":
    main()