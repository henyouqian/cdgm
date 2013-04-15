import g
import time
import csv
import __builtin__

# simple profile
class Tm(object):
    def __init__(self):
        self._start = time.time()

    def prt(self, text):
        return
        t = time.time()
        print("%s: %f" %(text, t-self._start))
        self._start = t

# parse csv file
class CsvTbl(object):
    def __init__(self, csvpath, keycol):
        self.header = {}    # {colName:colIndex}
        self.body = {}
        with open(csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True
            keycolidx = None
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    for colname in row:
                        if colname == keycol:
                            keycolidx = i
                        self.header[colname] = i
                        i += 1
                    if keycolidx == None:
                        raise ValueError("key column not found:" + keycol)
                else:
                    self.body[row[keycolidx]] = row

    def get_row(self, key):
        return self.body[str(key)]

    def get_value(self, row, colname):
        return row[self.header[colname]]

    def get_values(self, row, *colnames):
        return (row[self.header[colname]] for colname in colnames)

    def get(self, rowkey, colname):
        return self.body[str(rowkey)][self.header[colname]]

    def gets(self, rowkey, *colnames):
        row = self.get_row(rowkey)
        return self.get_values(row, *colnames)

class CsvTblMulKey(object):
    def __init__(self, csvpath, *keycols):
        self.header = {}    # {colName:colIndex}
        self.body = {}
        with open(csvpath, 'rb') as csvfile:
            spamreader = csv.reader(csvfile)
            firstrow = True
            keycolidx = None
            for row in spamreader:
                if firstrow:
                    firstrow = False
                    i = 0
                    for colname in row:
                        self.header[colname] = i
                        i += 1
                    keycolids = tuple(self.header[keycol] for keycol in keycols)
                else:
                    self.body[tuple(row[colidx] for colidx in keycolids)] = row

    def get_row(self, *keys):
        keys = tuple(str(key) for key in keys)
        return self.body[keys]

    def get_value(self, row, colname):
        return row[self.header[colname]]

    def get(self, rowkeys, colname):
        rowkeys = tuple(str(key) for key in rowkeys)
        return self.body[rowkeys][self.header[colname]]


def lower_bound(haystack, needle, lo = 0, hi = None, cmp = None, key = None):
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
    if cmp is None: cmp = __builtin__.cmp
    if key is None: key = lambda x: x
    if lo < 0: raise ValueError( 'lo cannot be negative' )
    if hi is None: hi = len(haystack)

    val = None
    while lo < hi:
        mid = (lo + hi) >> 1
        val = cmp(key(haystack[mid]), needle)
        if val < 0:
            lo = mid + 1
        else:
            hi = mid
    if val is None: return -1
    elif val == 0: return lo
    elif lo >= len(haystack): return -1 - lo
    elif cmp(key(haystack[lo]), needle) == 0: return lo
    else: return -1 - lo

def upper_bound(haystack, needle, lo = 0, hi = None, cmp = None, key = None):
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
    if cmp is None: cmp = __builtin__.cmp
    if key is None: key = lambda x: x
    if lo < 0: raise ValueError( 'lo cannot be negative' )
    if hi is None: hi = len(haystack)

    val = None
    while lo < hi:
        mid = (lo + hi) >> 1
        val = cmp(key(haystack[mid]), needle)
        if val > 0:
            hi = mid
        else:
            lo = mid + 1
    if val is None: return -1
    elif val == 0: return lo
    elif lo > 0 and cmp(key(haystack[lo - 1]), needle) == 0: return lo
    else: return -1 - lo


import datetime

_local_server_delta_time = None
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

def utc_now():
    local_datetime = datetime.datetime.utcnow()
    return local_datetime + _local_server_delta_time

def datetime_to_str(dt):
    return datetime.datetime.strftime(dt, "%Y-%m-%d %H:%M:%S")

def parse_datetime(str_datetime):
    return datetime.datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S")