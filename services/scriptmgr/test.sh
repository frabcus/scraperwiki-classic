#!/bin/sh
# Tests for scriptmgr
# scriptmgr should be already running.

usage="test.sh [-c count]"

count=90

# Option parsing
case $1 in
  (-c) count=$2;shift 2;;
  *) break;;
esac


for i in $(awk 'BEGIN{for(i=1;i<='$count';++i)print i}')
do
    echo 'Running' $i
    data="code=import time;print 1-2;time.sleep(10);print 'hello'&run_id=$i&scrapername=test&scraper_id=$i&language=python"
    length=${#data}
    set -x
    curl -H "Content-Length: $length" -d "$data" http://127.0.0.1:9001/Execute &
    set +x
done

echo ''
echo ''

