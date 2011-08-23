route add default gw 10.0.0.1 eth0 > /dev/null
export PHPPATH='/home/scraperwiki'
su scriptrunner -c "cd ~;/home/startup/exec.php --script script.py --ds $1 --runid $2"

