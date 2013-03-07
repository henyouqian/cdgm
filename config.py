debug = True

server_port = 8888

redis = {
    "host": "localhost",
    "port": 6379,
}

db = {
    "driver": "psycopg2",
    "host": "localhost",
    "database": "account_db",
    "user": "postgres",
    "password": "Nmmgb808313",
    "num_threads": 3,
    "tx_connection_pool_size": 2,
    "queue_timeout": 1,
}