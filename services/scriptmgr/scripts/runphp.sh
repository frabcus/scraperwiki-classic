route add default gw 10.0.0.1 eth0 > /dev/null
export PHPPATH='/home/scraperwiki/php:$PHPPATH'
su scriptrunner -c "cd ~;/home/startup/exec.php --script=/home/scriptrunner/script.php --ds=$1 --runid=$2 --scrapername=$3 --qs=$4"

