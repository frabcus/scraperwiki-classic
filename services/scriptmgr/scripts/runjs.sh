route add default gw 10.0.0.1 eth0 > /dev/null
export NODE_PATH='/usr/local/lib/node_modules:/home/scraperwiki/javascript:/home/scriptrunner'
SN=$3
if [ -n $SN ]; then 
	SN="--scrapername ${SN}" 
	echo "SN is now"
	echo $SN		
fi
su scriptrunner -c "cd ~;ulimit -t 80;/home/startup/exec.js --script /home/scriptrunner/script.js --ds $1 --runid $2 $SN"