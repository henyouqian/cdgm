import os
import shutil

os.system("""
	apt-get install rrdtool librrds-perl librrd2-dev python-dev libapr1-dev libconfuse-dev libpcre3-dev
	apt-get install ganglia-webfrontend
	tar -xf ganglia-web-3.5.7.tar.gz
	cd ganglia-web-3.5.7
	make install
""")

shutil.copy("ganglia.nginx", "/etc/nginx/sites-enabled")
os.system("nginx -s reload")
