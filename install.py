import os
import imp

def app_exists(app):
    for cmdpath in os.environ['PATH'].split(':'):
        if os.path.isdir(cmdpath): #check if some folder does not exist
            if app in os.listdir(cmdpath):
                return True
    else:
        return False


def mdl_exists(mdl):
    try:
        imp.find_module(mdl)
    except:
        return False
    else:
        return True

def install_app(apt_name):
	os.system("sudo apt-get install %s" % apt_name)
		

def install_mdl(mdl_name):
    os.system("sudo pip install %s" % mdl_name)

if __name__ == "__main__":
    os.system("sudo easy_install -U distribute")

    install_app("python-dev")
    os.system("sudo apt-get build-dep python-mysqldb")
    install_app("python-pip")
    install_mdl("virtualenv")

    if not os.path.exists("env"):
    	os.system("virtualenv env")
    os.system(". env/bin/activate")

    install_mdl("tornado")
    install_mdl("mysql-python")
