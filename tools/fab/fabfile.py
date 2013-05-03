from fabric.api import env, sudo, put, local, get

env.hosts = ["42.121.107.155"]
env.user = 'root'
env.password = 'Nmmgb808313'

def test():
	put("install.py", "./")
	sudo("python install.py")
	sudo("rm install.py")
