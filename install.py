import os
import imp

def app_exists(app):
    for cmdpath in os.environ['PATH'].split(':'):
        if os.path.isdir(cmdpath): #check if some folder does not exist
            if app in os.listdir(cmdpath):
                return True
    else:
        return False


def module_exists(mdl):
    try:
        imp.find_module(mdl)
    except:
        return False
    else:
        return True

def install_app(apt_name):
    os.system("sudo apt-get install %s" % apt_name)


def install_module(mdl_name):
    os.system("sudo env/bin/pip install %s" % mdl_name)

if __name__ == "__main__":
    install_app("python-dev")
    os.system("sudo apt-get build-dep python-mysqldb")
    install_app("python-pip")
    os.system("sudo pip install virtualenv")

    if not os.path.exists("env"):
        os.system("virtualenv env")
    os.system(". env/bin/activate")

    install_module("tornado")
    os.system("sudo easy_install -U distribute")
    install_module("mysql-python")
    install_module("redis")
    install_module("hiredis")
    install_module("futures")
