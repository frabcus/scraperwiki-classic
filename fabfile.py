# globals
config.project_name = 'project_name'

# environments
def dev():
    "On the scrpaerwiki server, accessible from http://dev.scraperwiki.com"
    config.fab_hosts = ['212.84.75.28']
    config.path = '/var/www/dev.scraperwiki.com'
    config.web_path = 'file:///home/scraperwiki/scraperwiki'
    config.activate = config.path + '/bin/activate'
    config.fab_user = 'scraperdeploy'
    config.virtualhost_path = "/"

def alpha():
    "On the scrpaerwiki server, accessible from http://alpha.scraperwiki.com"
    config.fab_hosts = ['212.84.75.28']
    config.path = '/var/www/alpha.scraperwiki.com'
    config.web_path = 'file:///home/scraperwiki/scraperwiki'
    config.activate = config.path + '/bin/activate'
    config.fab_user = 'scraperdeploy'
    config.virtualhost_path = "/"


def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """

    require('path')
    sudo('hg clone file:///home/scraperwiki/scraperwiki $(path)')        
    sudo('chown -R %s %s' % (config.fab_user, config.path))
    sudo('cd $(path); easy_install virtualenv')
    run('hg clone $(web_path) $(path)', fail='ignore')
    run('cd $(path); virtualenv --no-site-packages .')
    virtualenv('easy_install pip')

    deploy()

def virtualenv(command):
    run('cd $(path); source ' + config.activate + '&&' + command)


def buildout():
  virtualenv('python bootstrap.py')
  virtualenv('buildout')


def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """
    
    print "***************** DEPLOY *****************"
    print "Please Enter your deploy message: \r"
    message = raw_input()

    require('path')
    import time
    config.release = time.strftime('%Y%m%d%H%M%S')
    
    run('cd $(path); hg pull; hg update -C')
    
    buildout()
    migrate()
    restart_webserver()    

    sudo("""
    echo "%s" | mail -s "New Scraperwiki Deployment" scrapewiki-commits@googlegroups.com -- -f mercurial@scraperwiki.com
    """ % message)

    
def migrate():
  virtualenv('cd web; python manage.py syncdb')
  virtualenv('cd web; python manage.py migrate')

def restart_webserver():
    "Restart the web server"
    sudo('apache2ctl restart')







