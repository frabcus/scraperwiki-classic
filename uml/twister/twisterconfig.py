import optparse
import logging, logging.config
import time
import ConfigParser

try:
    import cloghandler
except:
    pass


def jstime(dt):
    return str(1000*int(time.mktime(dt.timetuple()))+dt.microsecond/1000)


parser = optparse.OptionParser()
parser.add_option("--pidfile")
parser.add_option("--config")
parser.add_option("--logfile")
parser.add_option("--setuid", action="store_true")
poptions, pargs = parser.parse_args()

config = ConfigParser.ConfigParser()
config.readfp(open(poptions.config))

djangokey = config.get("twister", "djangokey")
djangourl = config.get("twister", "djangourl")

nodecontrollername = "lxc001"
nodecontrollerhost = config.get(nodecontrollername, 'host')
nodecontrollerport = config.getint(nodecontrollername, 'via')

    # primarily to pick up syntax errors
stdoutlog = poptions.logfile and open(poptions.logfile+"-stdout", 'a', 0)  

logger = logging.getLogger('twister')
