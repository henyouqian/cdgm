import time

class Tm(object):
    def __init__(self):
        self._start = time.time()

    def prt(self, text):
        return
        t = time.time()
        print("%s: %f" %(text, t-self._start))
        self._start = t