import os
import conf

os.chdir(conf.proj_root+"install")

os.system("""
	tar -xf ganglia-3.5.0.tar.gz
	cd ganglia-3.5.0
	./configure
	make
	make install
""")