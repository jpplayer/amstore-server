#!/bin/bash 

LOGFILE=/var/log/amstore.log

function getdir() {
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
echo $DIR
}

DIR=`getdir`
$DIR/start.py >> $LOGFILE 2>&1 &
echo "Started amstore on port 8025. Log file is $LOGFILE."
