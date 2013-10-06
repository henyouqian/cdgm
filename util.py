import config
import brukva
import adb
import adisp
import aredis
import time
import csv
import random
import logging
import os
from tornado import options
import toredis
import gamedata
import json
import __builtin__


# simple profile
class Tm(object):
    def __init__(self):
        self._start = time.time()

    def prt(self, text):
        return
        t = time.time()
        print("%s: %f" % (text, t - self._start))
        self._start = t


# parse csv file
class CsvTbl(object):
    def __init__(self, csvpath, keycol):
        self.csvpath = csvpath
        self.keycol = keycol
        self.reload()

    def reload(self):
        self.header = {}    # {colName:colIndex}
        self.body = {}
        with open(self.csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True
            keycolidx = None
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    for colname in row:
                        if colname == self.keycol:
                            keycolidx = i
                        self.header[colname] = i
                        i += 1
                    if keycolidx is None:
                        raise ValueError("key column not found:" + self.keycol)
                else:
                    self.body[row[keycolidx]] = row

    def get_row(self, key):
        return self.body.get(str(key))

    def get_value(self, row, colname):
        return row[self.header[colname]]

    def get_values(self, row, *colnames):
        return (row[self.header[colname]] for colname in colnames)

    def get(self, rowkey, colname):
        return self.body[str(rowkey)][self.header[colname]]

    def gets(self, rowkey, *colnames):
        row = self.get_row(rowkey)
        return self.get_values(row, *colnames)

    def iter_rowkeys(self):
        return tuple(self.body.iterkeys())


class CsvTblMulKey(object):
    def __init__(self, csvpath, *keycols):
        self.csvpath = csvpath
        self.keycols = keycols
        self.reload()

    def reload(self):
        self.header = {}    # {colName:colIndex}
        self.body = {}
        with open(self.csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    for colname in row:
                        self.header[colname] = i
                        i += 1
                    keycolids = tuple(self.header[keycol] \
                                        for keycol in self.keycols)
                else:
                    self.body[tuple(row[colidx]     \
                        for colidx in keycolids)] = row

    def get_row(self, *keys):
        keys = tuple(str(key) for key in keys)
        return self.body[keys]

    def get_value(self, row, colname):
        return row[self.header[colname]]

    def get(self, rowkeys, colname):
        rowkeys = tuple(str(key) for key in rowkeys)
        return self.body[rowkeys][self.header[colname]]

def parse_csv(csvfile):
    first_row = []
    tbl = []
    with open(csvfile, 'rb') as csvfile:
        spamreader = csv.reader(csvfile)
        for row in spamreader:
            if not first_row:
                first_row = row
            else:
                dict_row = dict(zip(first_row, row))
                tbl.append(dict_row)
    return tbl


def lower_bound(haystack, needle, lo=0, hi=None, cmp=None, key=None):
    """lower_bound(haystack, needle[, lo = 0[, hi = None[, cmp = None[, key = None]]]]) => n

    Find var{needle} via a binary search on var{haystack}.  Returns the
    index of the first match if var{needle} is found, else a negative
    value var{N} is returned indicating the index where var{needle}
    belongs with the formula "-var{N}-1".

    var{haystack} - the ordered, indexable sequence to search.
    var{needle} - the value to locate in var{haystack}.
    var{lo} and var{hi} - the range in var{haystack} to search.
    var{cmp} - the cmp function used to order the var{haystack} items.
    var{key} - the key function used to extract keys from the elements.
    """
    if cmp is None:
        cmp = __builtin__.cmp
    if key is None:
        key = lambda x: x
    if lo < 0:
        raise ValueError('lo cannot be negative')
    if hi is None:
        hi = len(haystack)

    val = None
    while lo < hi:
        mid = (lo + hi) >> 1
        val = cmp(key(haystack[mid]), needle)
        if val < 0:
            lo = mid + 1
        else:
            hi = mid
    if val is None:
        return -1
    elif val == 0:
        return lo
    elif lo >= len(haystack):
        return -1 - lo
    elif cmp(key(haystack[lo]), needle) == 0:
        return lo
    else:
        return -1 - lo


def upper_bound(haystack, needle, lo=0, hi=None, cmp=None, key=None):
    """upper_bound(haystack, needle[, lo = 0[, hi = None[, cmp = None[, key = None]]]]) => n

    Find var{needle} via a binary search on var{haystack}.  Returns the
    non-negative index var{N} of the element that immediately follows the
    last match of var{needle} if var{needle} is found, else a negative
    value var{N} is returned indicating the index where var{needle}
    belongs with the formula "-var{N}-1".

    var{haystack} - the ordered, indexable sequence to search.
    var{needle} - the value to locate in var{haystack}.
    var{lo} and var{hi} - the range in var{haystack} to search.
    var{cmp} - the cmp function used to order the var{haystack} items.
    var{key} - the key function used to extract keys from the elements.
    """
    if cmp is None:
        cmp = __builtin__.cmp
    if key is None:
        key = lambda x: x
    if lo < 0:
        raise ValueError('lo cannot be negative')
    if hi is None:
        hi = len(haystack)

    val = None
    while lo < hi:
        mid = (lo + hi) >> 1
        val = cmp(key(haystack[mid]), needle)
        if val > 0:
            hi = mid
        else:
            lo = mid + 1
    if val is None:
        return -1
    elif val == 0:
        return lo
    elif lo > 0 and cmp(key(haystack[lo - 1]), needle) == 0:
        return lo
    else:
        return -1 - lo


import datetime


_local_server_delta_time = None
_local_server_delta_sec = 0

def sync_time():
    import MySQLdb
    import config
    conn = MySQLdb.connect(db=config.wh_db["database"],
                           user=config.wh_db["user"],
                           passwd=config.wh_db["password"],
                           host=config.wh_db["host"],
                           port=3306)
    cursor = conn.cursor()
    cursor.execute("SELECT UTC_TIMESTAMP()", None)
    rows = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()

    server_datetime = rows[0][0]
    local_datetime = datetime.datetime.utcnow()
    global _local_server_delta_time
    _local_server_delta_time = server_datetime - local_datetime
    _local_server_delta_sec = _local_server_delta_time.total_seconds()


def utc_now():
    local_datetime = datetime.datetime.utcnow()
    return local_datetime + _local_server_delta_time


def datetime_to_str(dt):
    return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")


def parse_datetime(str_datetime):
    return datetime.datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S")


def utc_now_sec():
    return time.time() + _local_server_delta_sec

# reply
def new_reply():
    return {"error": ""}

# 
class WeightedRandom(object):
    def __init__(self, totalWeight, *weights):
        """if totalWeight <= 0, auto sum weights as totalWeight"""
        sum = 0
        uppers = []
        for weight in weights:
            sum += weight
            uppers.append(sum)
        if totalWeight > 0:
            sum = totalWeight
        self.uppers = [x/float(sum) for x in uppers]

    def get(self):
        rdm = random.random()
        idx = 0
        for upper in self.uppers:
            if rdm <= upper:
                return idx
            idx += 1
        return -1

# redis
redis_pool = []
redis_time_diff = 0

import redis as sredis

def init_redis():
    for __ in xrange(2):
        c = brukva.Client(**config.redis)
        c.connect()
        redis_pool.append([c, time.time()+config.redis_conn_life])

    global redis_time_diff
    r = sredis.StrictRedis(**config.redis)
    redisTime, _ = r.time()
    redis_time_diff = int(redisTime - time.time())

def redis():
    ct = random.choice(redis_pool)
    if (not ct[0].connection.connected()) or time.time() > ct[1]:
        # ct[0].disconnect()
        ct[0] = brukva.Client(**config.redis)
        ct[0].connect()
        ct[1] = time.time() + config.redis_conn_life

    return ct[0].async

def redis_pipe():
    ct = random.choice(redis_pool)
    if (not ct[0].connection.connected()) or time.time() > ct[1]:
        # ct[0].disconnect()
        ct[0] = brukva.Client(**config.redis)
        ct[0].connect()
        ct[1] = time.time() + config.redis_conn_life
    return ct[0].pipeline()

def redis_pipe_execute(pipe):
    return adisp.async(pipe.execute, cbname='callbacks')()

# database
authdb = None
whdb = None
kvdb = None
ar = None
toredis_pool = None

def init_db(): 
    global authdb, whdb, kvdb, ar, toredis_pool
    authdb = adb.Database(**config.auth_db)
    whdb = adb.Database(**config.wh_db)
    kvdb = adb.Database(**config.kv_db)
    ar = aredis.Redis()
    toredis_pool = toredis.client.ClientPool()


def stop_db():
    global authdb, whdb, kvdb, ar, toredis_pool
    authdb.stop()
    whdb.stop()
    kvdb.stop()
    ar.stop()

    del toredis_pool

def tr():
    global toredis_pool
    return toredis_pool.get_client()

# logging
def init_logger(debug):
    # command line and esay enable logging
    options.parse_command_line()

    try:
        os.makedirs("log")
    except OSError:
        pass

    logger = logging.getLogger()
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    # write to file and rollover at midnight
    FORMAT = '[%(levelname)s %(asctime)-15s %(filename)s:%(levelno)s] %(message)s'
    formatter = logging.Formatter(fmt=FORMAT)

    handler = logging.handlers.TimedRotatingFileHandler("log/wh.log", when='midnight', interval=1)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# kv

def getRedisTimeUnix():
    return int(time.time())+redis_time_diff

@adisp.async
@adisp.process
def setkv(key, value, callback):
    expireTime = getRedisTimeUnix() + gamedata.CACHE_LIFE_SEC
    v = json.dumps(value)

    pipe = redis_pipe()
    k = "kv/"+key
    pipe.set(k, v)
    pipe.zadd("kvz", expireTime, k)
    yield redis_pipe_execute(pipe)
    callback(None)
    

@adisp.async
@adisp.process
def getkv(key, callback):
    k = "kv/"+key
    v = yield redis().get(k)

    if v:
        callback(json.loads(v))
        return
    else:
        rows = yield util.kvdb.runQuery(
            """ SELECT v FROM kvs WHERE k=%s"""
            ,(key, )
        )
        row = rows[0]
        if not row:
            callback(None)
            return

        # write to redis
        expireTime = getRedisTimeUnix() + gamedata.CACHE_LIFE_SEC

        pipe = redis_pipe()
        k = "kv/"+key
        pipe.set(k, row[0])
        pipe.zadd("kvz", expireTime, k)
        yield util.redis_pipe_execute(pipe)

        callback(json.loads(row[0]))
        return
