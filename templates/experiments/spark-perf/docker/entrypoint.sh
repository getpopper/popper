#!/bin/bash

function stopall {
  # stop slaves
  stopsshd "`cat /spark/conf/slaves`"

  # stop our sshd
  service ssh stop

  exit $1
}

function zero_or_die {
  if [ $1 -ne 0 ]; then
    stopall $1
  fi
}

echo 'Host *' > /root/.ssh/config
echo 'StrictHostKeyChecking no' >> /root/.ssh/config
echo 'LogLevel quiet' >> /root/.ssh/config
echo "Port $SSHD_PORT" >> /root/.ssh/config

echo 'log4j.rootCategory=WARN, console' > /spark/conf/log4j.properties

if [ -n "$MASTER" ] ; then

  # send sshd to background
  /root/.ssh/entrypoint.sh &> /dev/null &

  # wait for other's sshd to startup
  if [ -z "$WAIT_SSHD_SECS" ] ; then
    WAIT_SECS=60
  fi
  sleep $WAIT_SSHD_SECS

  # start spark cluster
  /spark/sbin/start-all.sh

  zero_or_die $?

  # check if MASTER hostname was given and use hostname if not
  if [ -z "$MASTER_HOSTNAME" ] ; then
    MASTER_HOSTNAME=`hostname`
  fi
  echo "spark.master=spark://$MASTER_HOSTNAME:7077" > /spark/conf/spark-defaults.conf
  echo 'spark.eventLog.enabled=false' >> /spark/conf/spark-defaults.conf

  # run given command
  "$@" &> /tmp/spark-output

  stopall $?
else
  /root/.ssh/entrypoint.sh &> /dev/null
  exit 0
fi
