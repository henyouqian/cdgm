import auth
import g
import config
import test

from tornado import web, httpserver, ioloop
from tornado import options
import brukva
from adb import Database
import logging
import os

def main():
    print "Server starting..."

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
    g.db = Database(**config.db)
    
    # application
    application = web.Application(
        auth.handlers
        +test.handlers,
        debug = config.debug
    )
    application.listen(params.port)
    if (config.debug):
        logging.getLogger().setLevel(logging.DEBUG)
        options.enable_pretty_logging()
        print "Server start in debug mode"
    else:
        logging.disable(logging.WARNING)
        print "Server start"

    # server loop
    try:
        ioloop.IOLoop.instance().start()
    except:
        print "Server shutting down..."
        g.db.stop()

if __name__ == "__main__":
    main()