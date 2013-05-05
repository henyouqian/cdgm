import os
import subprocess

work_dir = "/home/wh/cdgm"
os.chdir(work_dir)

# os.system("git pull")

os.system("env/bin/python server.py &")