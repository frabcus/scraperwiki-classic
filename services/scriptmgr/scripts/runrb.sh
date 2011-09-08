route add default gw 10.0.0.1 eth0 > /dev/null
export RUBYLIB='/home/scraperwiki/ruby/scraperwiki/lib'
su scriptrunner -c "cd ~;/home/startup/exec.rb --script=/home/scriptrunner/script.rb --ds=$1 --runid=$2 --scrapername=$3 --qs=$4"
