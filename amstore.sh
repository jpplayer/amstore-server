
FOLDER="$PWD"

function usage() {
	echo 'amstore start|stop|restart|status'
	exit 1

}


function start() {
     nohup $FOLDER/start.py >> /var/log/amstore.log 2>&1 &
     (ps -o pgid= "$!" | grep -o '[0-9]*') > /var/run/amstore.pid
     cat  /var/run/amstore.pid
}

function stop() {
      kill -- -$(cat /var/run/amstore.pid)
      echo "" > /var/run/amstore.pid
}

case "$1" in
	start)
		start
	;;
	stop)
		stop
	;;
	restart)
		stop
		start
	;;
	status)
		ps -ef | grep $(cat /var/run/amstore.pid) || echo 'Amstore is stopped.'
	;;
	*)
		usage
	;;
esac
