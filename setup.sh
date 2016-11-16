#!/bin/bash

# Centos
if [[ -f /etc/redhat-release ]]; then
yum install -y gcc epel-release python-pip
systemctl stop firewalld
# Ubuntu
elif [[ -f /etc/debian_version ]]; then
apt install -y gcc python-pip
ufw disable
fi

# Create user amstore if not exists
id -u amstore &>/dev/null || useradd amstore

# Ensure amstore user has access to files
chown -R amstore .

# Create app folders
mkdir -p /var/lib/amstore/APPS
mkdir -p /var/lib/amstore/TMP
chown -R amstore /var/lib/amstore

touch /var/run/amstore.pid
chown amstore /var/run/amstore.pid

touch /var/log/amstore.log
chown amstore /var/log/amstore.log

# Install flask
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


