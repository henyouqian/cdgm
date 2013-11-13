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
* cp -rf go /usr/local/
* vim ~/.bashrc and append:
	export GOPATH=$HOME/go
	export PATH=$PATH:$GOPATH/bin

	export GOROOT=/usr/local/go
	export PATH=$PATH:$GOROOT/bin

-- nginx
* apt-get install nginx
* cp /home/cdgm/wh.nginx /etc/nginx/sites-enabled/
* vim /etc/nginx/sites-enabled/wh.nginx
	edit path
* rm /etc/nginx/sites-enabled/default

-- https
* cd /etc/nginx
* sudo openssl genrsa -des3 -out server.key 1024
* sudo openssl req -new -key server.key -out server.csr
	Common Name (e.g. server FQDN or YOUR name) 要填的跟url访问地址一致
* sudo cp server.key server.key.org
* sudo openssl rsa -in server.key.org -out server.key
* sudo openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
