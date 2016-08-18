#!/bin/bash 

WORKDIR=/home/amstore/amstore-server
#VIRTUALENV_DIR=$WORKDIR/flask
LOGFILE=/var/log/amstore.log

#source $VIRTUALENV_DIR/bin/activate

cd $WORKDIR
exec ./start.py >> $LOGFILE 2>&1 & 
