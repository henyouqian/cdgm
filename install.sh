apt-get install python-pip
pip install virtualenv
virtualenv env
. env/bin/activate

pip install tornado
pip install simplejson

apt-get install python-dev
#easy_install psycopg2

apt-get build-dep python-mysqldb
pip install mysql-python

cd brukva
python setup.py install
cd ..
