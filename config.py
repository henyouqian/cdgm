﻿debug = True
auto_auth = True and debug
app_id = 112233 #fixme: should be generated by adding a app by developer
cookie_secret = "da39a3ee5e6b4b0d3255bfef95601890afd80709"
app_id_91 = 106848
app_secret_91 = "6728657e0097fdaf9fdb1d2aa59016d1e5bb68f65b5af774"

redis = {
    "host": "127.0.0.1",
    # "host": "42.121.107.155",
    "port": 6379,
}
redis_conn_life = 60 * 2

# auth_db = {
#     "driver": "psycopg2",
#     "host": "localhost",
#     "database": "account_db",
#     "user": "postgres",
#     "password": "Nmmgb808313",
#     "num_threads": 3,
#     "tx_connection_pool_size": 2,
#     "queue_timeout": 1,
#     "thread_idle_life": 60*60,
# }

auth_db = {
    "driver": "MySQLdb",
    "host": "localhost",
    "database": "account_db",
    "user": "root",
    "password": "",
    "num_threads": 1,
    "tx_connection_pool_size": 1,
    "queue_timeout": 1,
    "thread_idle_life": 60*60,
}

# auth_db = {
#     "driver": "MySQLdb",
#     "host": "henyouqian.mysql.rds.aliyuncs.com",
#     "database": "account_db",
#     "user": "liwei",
#     "password": "nmmgb808313",
#     "num_threads": 20,
#     "tx_connection_pool_size": 15,
#     "queue_timeout": 1,
# }

wh_db = {
    "driver": "MySQLdb",
    "host": "localhost",
    "database": "wh_db",
    "user": "root",
    "password": "",
    "num_threads": 1,
    "tx_connection_pool_size": 1,
    "queue_timeout": 1,
    "thread_idle_life": 60*60,
}

kv_db = {
    "driver": "MySQLdb",
    "host": "localhost",
    "database": "kv_db",
    "user": "root",
    "password": "",
    "num_threads": 1,
    "tx_connection_pool_size": 1,
    "queue_timeout": 1,
    "thread_idle_life": 60*60,
}
