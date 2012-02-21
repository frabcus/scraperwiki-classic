#!/bin/sh
# Tests for scriptmgr.
# scriptmgr should be already running.

usage="test.sh [-s] [-c count]"

count=90
sync=

# Option parsing
while true
do
  case $1 in
    (-c) count=$2;shift 2;;
    (-s) sync=yes;shift 1;;
    *) break;;
  esac
done

countN () {
    # Output a list of numbers from 1 to $1
    awk 'BEGIN{for(i=1;i<='$1';++i)print i}'
}

Execute () {
    # Send the Execute command to the scripmgr server, using $1
    # as the body of the command.
    set -x
    curl -d "$1" http://127.0.0.1:9001/Execute
    set +x
}


for i in $(countN "$count")
do
    echo 'Running' $i
    # Templated JSON object passed to Execute
    data=$( cat <<!
{
    "runid" : "$i",
    "code": "import time;print 1-2;time.sleep(10);print 'hello'",
    "scrapername": "test",
    "scraperid": "$i",
    "language": "python"
}
!
)
    if [ -n "$sync" ]
    then
        Execute "$data"
    else
        Execute "$data" &
    fi
done

echo ''
echo ''

