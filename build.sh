yum install -y gcc python-pip
pip install virtualenv
virtualenv flask

flask/bin/pip install flask
flask/bin/pip install flask-login
flask/bin/pip install flask-openid
flask/bin/pip install flask-mail
flask/bin/pip install flask-sqlalchemy
flask/bin/pip install sqlalchemy-migrate
flask/bin/pip install flask-whooshalchemy
flask/bin/pip install flask-wtf
flask/bin/pip install flask-babel
flask/bin/pip install guess_language
flask/bin/pip install flipflop
flask/bin/pip install coverage
flask/bin/pip install pyyaml
flask/bin/pip install flask-httpauth

mkdir -p /var/lib/amstore/APPS
mkdir -p /var/lib/amstore/TMP

service iptables stop
