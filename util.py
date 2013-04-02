import time
import csv

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
        return self.body[keys]

    def get_value(self, row, colname):
        return row[self.header[colname]]

    def get(self, rowkeys, colname):
        return self.body[rowkeys][self.header[colname]]