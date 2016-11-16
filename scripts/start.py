#!flask/bin/python
from app import app
app.run(host='0.0.0.0',port=5025,debug=False,threaded=True)
