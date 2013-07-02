import time

class g:
    pass

g.data = {}

def begin(name):
    if name not in g.data:
        g.data[name] = [0, 0]
    g.data[name][1] = time.time()

def end(name):
    d = g.data[name]
    d[0] += time.time() - d[1]

def print_all():
    print "~~~~~~~~~~~~~~~~~~~~~~~~"
    for k, v in g.data.iteritems():
        print k, v[0]
        v[0] = 0

    print "------------------------"
