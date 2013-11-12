* apt-get update
* apt-get upgrade
* apt-get install git
* git clone https://github.com/henyouqian/cdgm.git
* apt-get install python-dev
* apt-get build-dep python-mysqldb
* apt-get install python-pip
* pip install virtualenv
* env/bin/pip install tornado
* easy_install -U distribute
* env/bin/pip install mysql-python
* env/bin/pip install redis
* env/bin/pip install hiredis
* env/bin/pip install futures

-- redis
* cd /tmp/
* wget http://download.redis.io/releases/redis-2.6.16.tar.gz
* tar xzf redis-2.6.16.tar.gz
* cd redis-2.6.16/
* make
* make install
* screen -S redis
* /usr/local/bin/redis-server

-- mysql
* apt-get install mysql-server-5.5
* no password
* create database
* use database
* source sql/<every>.sql

-- go
* cd /tmp/
* wget https://go.googlecode.com/files/go1.1.2.linux-amd64.tar.gz
* tar xzf go1.1.2.linux-amd64.tar.gz
* cd go/

