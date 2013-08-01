* mysql-/etc/mysql/my.cnf
	innodb_buffer_pool_size=200M
	innodb_additional_mem_pool_size=20M

	log-slow-queries = /var/lib/mysql/slow-queries.log
	long_query_time = 1
	log-slow-admin-statements
