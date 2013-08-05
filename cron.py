#! ./env/bin/python
import time
import util
import os
import sys
from threading import Timer, current_thread

def work1():
    print "work1", current_thread()
    Timer(1, work1, ()).start()

def work2():
    print "work2", current_thread()
    Timer(1.12, work2, ()).start()

def main():
    print "main begin", current_thread()
    work1()
    work2()
    print "main end"

def getLock():
    pid = str(os.getpid())
    pidfile = "/tmp/wh_cron.pid"

    if os.path.isfile(pidfile):
        print "already running"
        sys.exit()
    else:
        open(pidfile, 'w').write(pid)

        def exitfunc():
            os.unlink(pidfile)

        import atexit
        atexit.register(exitfunc)
    

if __name__ == "__main__":
    getLock()
    main()

