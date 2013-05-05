from fabric.api import env, sudo, put, local, get

env.hosts = ["121.199.15.152", "121.199.15.151"]
# env.hosts = ["42.121.107.155"]
# env.hosts = ["localhost"]
env.user = 'root'
env.password = 'Nmmgb808313'

def do_script(filename):
	put(filename, "./")
	sudo("python " + filename)
	sudo("rm " + filename)

def wh_setup():
	do_script("wh_setup.py")

def wh_deploy():
	do_script("wh_deploy.py")
