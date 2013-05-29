$ cd /etc/nginx
$ openssl genrsa -des3 -out server.key 1024
$ openssl req -new -key server.key -out server.csr
* Common Name (e.g. server FQDN or YOUR name) 要填的跟url访问地址一致
$ cp server.key server.key.org
$ openssl rsa -in server.key.org -out server.key
$ openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
