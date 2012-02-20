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
    # Templated JSON object passed to /Execute
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
    length=${#data}
    set -x
    curl -H "Content-Length: $length" -d "$data" http://127.0.0.1:9001/Execute &
    set +x
done

echo ''
echo ''

