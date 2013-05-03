import os
import shutil

# os.system("sudo apt-get update")
os.system("sudo apt-get -y -qq install git")
os.system("sudo apt-get -y -qq install python-dev")
os.system("sudo apt-get -y -qq build-dep python-mysqldb")
os.system("sudo apt-get -y -qq install python-pip")
os.system("sudo pip install virtualenv")

work_dir = "/home/wh"
try:
	os.makedirs(work_dir)
except:
	pass
os.chdir(work_dir)

try:
	shutil.rmtree(work_dir + "/env")
except:
	pass
os.system("virtualenv env")
os.system(". env/bin/activate")

os.system("pip install tornado")
os.system("pip install mysql-python")
