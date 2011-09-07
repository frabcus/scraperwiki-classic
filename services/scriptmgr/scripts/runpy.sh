route add default gw 10.0.0.1 eth0 > /dev/null
export PYTHONPATH='/home/scraperwiki/python'
su scriptrunner -c "cd ~;/home/startup/exec.py --script /home/scriptrunner/script.py --ds=$1 --runid=$2 --scrapername=$3  --qs=$4"

