route add default gw 10.0.0.1 eth0 > /dev/null
export RUBYLIB='/home/scraperwiki/ruby/scraperwiki/lib'
if [-n $4]
	export QUERY_STRING=$4
fi
su scriptrunner -c "cd ~;/home/startup/exec.rb --script=/home/scriptrunner/script.rb --ds=$1 --runid=$2 --scrapername=$3"
