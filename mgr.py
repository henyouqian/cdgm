from multiprocessing import Process
import wh
import time
import os
import signal
import util
import logging
from tornado import options

ports = [8888, 8889]

def check():
    logging.debug("in check")
    pass

if __name__ == '__main__':
    util.init_logger(True)

    procs = []
    for port in ports:
        p = Process(target=wh.main, args=[port])
        procs.append([p, port])
        p.daemon = True
        p.start()

    logging.debug("Prosess manager running")

    deads = []
    try:
        while 1:
            time.sleep(3)
            check()
    except KeyboardInterrupt:
        print "shut down"
    finally:
        logging.debug("Manager wait for exit")
        for p in deads:
            p.join()
