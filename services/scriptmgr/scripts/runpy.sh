route add default gw 10.0.0.1 eth0 > /dev/null
export PYTHONPATH='/home/scraperwiki'
export PYTHONUNBUFFERED=true
su scriptrunner -c "cd ~;/home/startup/exec.py --script script.py --ds $1 --runid $2"

