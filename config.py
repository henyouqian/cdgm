﻿debug = True
app_id = 112233 #fixme: should be generated by adding a app by developer
cookie_secret = "da39a3ee5e6b4b0d3255bfef95601890afd80709"

redis = {
    "host": "localhost",
    #"host": "192.168.0.112",
    "port": 6379,
}

# auth_db = {
#     "driver": "psycopg2",
#     "host": "localhost",
#     "database": "account_db",
#     "user": "postgres",
#     "password": "Nmmgb808313",
#     "num_threads": 3,
#     "tx_connection_pool_size": 2,
#     "queue_timeout": 1,
# }

auth_db = {
    "driver": "MySQLdb",
    "host": "localhost",
    "database": "account_db",
    "user": "root",
    "password": "Nmmgb808313",
    "num_threads": 3,
    "tx_connection_pool_size": 2,
    "queue_timeout": 1,
}

wh_db = {
    "driver": "MySQLdb",
    "host": "localhost",
    "database": "wh_db",
    "user": "root",
    "password": "Nmmgb808313",
    "num_threads": 3,
    "tx_connection_pool_size": 2,
    "queue_timeout": 1,
}