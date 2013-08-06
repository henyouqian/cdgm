#! ./env/bin/python
import datetime
import time
import util
import os
import sys
from threading import Timer, current_thread

Z_CRON_TASK = "Z_CRON_TASK"

def add_task(dt, taskname):
    t = time.mktime(dt.timetuple())
    yield util.redis().zadd(Z_CRON_TASK, t, taskname)

def check_task():
    t = time.time()
    tasks = yield util.redis().zrangebyscore(Z_CRON_TASK, 0, t)
    if tasks:
        print tasks
        yield util.redis().z


    Timer(1, check_update, ()).start()


def main():
    print "main begin", current_thread()
    check_update()
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

