import os

work_dir = "/home/wh/cdgm"
os.chdir(work_dir)

os.system("git pull")
os.system("cp -f config_aliyun.py config.py")

os.system("env/bin/python daemon.py stop")
os.system("env/bin/python daemon.py start")