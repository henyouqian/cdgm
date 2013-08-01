import time
import util

def run():
    while 1:
        try:
            time.sleep(1)
            print(time.time())
        except KeyboardInterrupt:
            print("cron exit")
            break
    


def sig_handler(signum, frame):
    raise KeyboardInterrupt

import signal
signal.signal(signal.SIGINT, sig_handler)

if __name__ == "__main__":
    run()