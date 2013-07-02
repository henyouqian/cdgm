from fabric.api import env, sudo, put, local, get

# env.hosts = ["121.199.15.152"]
# env.hosts = ["121.199.15.152", "121.199.15.151"]
env.hosts = ["42.121.107.155"]
# env.hosts = ["localhost"]
env.user = 'root'
env.password = 'Nmmgb808313'

root_dir = "/home/wh/cdgm/"

def a():
    put("data/events.csv", root_dir+"data")

def do_script(filename):
    put(filename, ".")
    sudo("python " + filename)
    sudo("rm " + filename)

def setup():
    do_script("sys_setup.py")

def deploy():
    do_script("deploy.py")

def gmetad():
    put_conf()
    do_script("gmetad.py")
