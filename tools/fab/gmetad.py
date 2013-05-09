import os
import conf

os.chdir(conf.proj_root+"install")

os.system("""
	apt-get install rrdtool librrds-perl librrd2-dev python-dev libapr1-dev libconfuse-dev  libpcre3-dev
	tar -xf ganglia-3.5.0.tar.gz
	cd ganglia-3.5.0
	./configure --with-gmetad
	make
	make install
""")
