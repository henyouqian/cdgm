import os
import shutil

# setup system
os.system("sudo apt-get update")
os.system("sudo apt-get -y -qq install git")
os.system("sudo apt-get -y -qq install python-pip")
os.system("sudo apt-get -y -qq install python-dev")
os.system("sudo apt-get -y -qq build-dep python-mysqldb")
os.system("sudo pip install virtualenv")
# os.system("easy_install -U distribute")

work_dir = "/home/wh"
try:
	os.makedirs(work_dir)
except:
	pass
os.chdir(work_dir)

# clone or pull cdgm from github
if not os.path.exists("cdgm"):
	os.system("git clone https://github.com/henyouqian/cdgm.git")
	
os.chdir("cdgm")

# install dependence
if not os.path.exists("env"):
	os.system("virtualenv env")

os.system("env/bin/pip install tornado")
os.system("env/bin/pip install mysql-python")