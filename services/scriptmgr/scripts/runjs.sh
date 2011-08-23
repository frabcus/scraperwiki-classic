route add default gw 10.0.0.1 eth0 > /dev/null
export NODE_PATH='/usr/local/lib/node_modules:/home/scraperwiki/javascript:/home/scriptrunner'
su scriptrunner -c "cd ~;/home/startup/exec.js --script /home/scriptrunner/script.js --ds $1 --runid $2"