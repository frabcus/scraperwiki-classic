route add default gw 10.0.0.1 eth0
su - scriptrunner -c "cd ~;exec.py -script=script.py -ds=$1 -runid=$2"

