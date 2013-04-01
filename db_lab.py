import config
from tornado import ioloop
from adb import Database
import adisp
from tornado.database import Connection
from itertools import repeat
from random import randint

def add_cards(n):
    # conn = yield test_db.beginTransaction()

    i = 0
    for __ in xrange(n):
        test_db.executemany(
            """ INSERT INTO cardEntities
                    (hp, atk, def, wis, agi, cardId, ownerId)
                    VALUES(%s, %s, %s, %s, %s, %s, %s)"""
            ,repeat((randint(1000, 10000), randint(1000, 10000), randint(1000, 10000), randint(1000, 10000), randint(1000, 10000), randint(0, 100), randint(1000, 1000000)), 10000)
        )
        print i
        i += 1
    # yield test_db.commitTransaction(conn)

if __name__ == '__main__':
    test_db = Connection("localhost",
                      "test",
                      "root",
                      "Nmmgb808313")

    try:
        add_cards(4000)
    except KeyboardInterrupt as e:
        print "KeyboardInterrupt."
    except Exception as e:
        print e
    finally:
        
        test_db.close();
        print "Done..."
