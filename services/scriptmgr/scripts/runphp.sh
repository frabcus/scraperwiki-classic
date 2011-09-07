route add default gw 10.0.0.1 eth0 > /dev/null
export PHPPATH='/home/scraperwiki/php:$PHPPATH'
if [-n $4]
	export QUERY_STRING=$4
fi
su scriptrunner -c "cd ~;/home/startup/exec.php --script=/home/scriptrunner/script.php --ds=$1 --runid=$2 --scrapername=$3"

