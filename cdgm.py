import auth
import g
import config
from tornado import web, httpserver, ioloop
from tornado import options
import brukva
from adb import Database
import logging

if __name__ == "__main__":
    # redis
    c = brukva.Client(**config.redis)
    c.connect()
    g.redis = c.async

    # database
    g.db = Database(**config.db)
    
    # application
    application = web.Application(
        auth.handlers,
        debug = config.debug
    )
    application.listen(config.server_port)
    if (config.debug):
        logging.getLogger().setLevel(logging.DEBUG)
        options.enable_pretty_logging()
        print "Server start in debug mode"
    else:
        print "Server start"

    # server loop
    try:
        ioloop.IOLoop.instance().start()
    except:
        print "Server shutting down..."
        g.db.stop()
