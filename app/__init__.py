#!flask/bin/python
from flask import Flask

UPLOAD_FOLDER = '/var/lib/amstore/TMP'
ALLOWED_EXTENSIONS = set(['tar.gz','tgz'])
APPS_FOLDER = '/var/lib/amstore/APPS'

app = Flask(__name__, static_url_path='/var/lib/amstore/APPS')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['APPS_FOLDER'] = APPS_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

from app import applications
