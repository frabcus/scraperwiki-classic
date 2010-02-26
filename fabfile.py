from fabric.api import *

# globals
PROJECT_NAME = 'ScraperWiki'

# environments
def dev():
    "On the scrpaerwiki server, accessible from http://dev.scraperwiki.com"
    env.hosts = ['212.84.75.28']
    env.path = '/var/www/dev.scraperwiki.com'
    env.branch = 'default'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.virtualhost_path = "/"
    env.deploy_version = "Dev"

def alpha():
    "On the scrpaerwiki server, accessible from http://alpha.scraperwiki.com"
    env.hosts = ['212.84.75.28']
    env.path = '/var/www/alpha.scraperwiki.com'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.virtualhost_path = "/"
    env.deploy_version = "Alpha"

def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """

    sudo('hg clone file:///home/scraperwiki/scraperwiki %s' % env.path)        
    sudo('chown -R %s %s' % (env.fab_user, env.path))
    sudo('cd %s; easy_install virtualenv' % env.path)
    run('hg clone %s %s', fail='ignore' % (env.web_path, env.path))
    run('cd %s; virtualenv --no-site-packages .' % env.path)
    virtualenv('easy_install pip')

    deploy()

def virtualenv(command):
    temp = 'cd %s; source ' % env.path
    run(temp + env.activate + '&&' + command)


def buildout():
  virtualenv('buildout')

def install_cron():
    virtualenv('crontab crontab')

def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """

    
    print "***************** DEPLOY *****************"
    print "Please Enter your deploy message: \r"
    message = raw_input()

    import time
    env.release = time.strftime('%Y%m%d%H%M%S')
    
    run('cd %s; hg pull; hg update -C %s' % (env.path, env.branch))
    
    buildout()
    migrate()
    install_cron()
    restart_webserver()   

    sudo("""
    echo "%s" | mail -s "New Scraperwiki Deployment to %s" scrapewiki-commits@googlegroups.com -- -f mercurial@scraperwiki.com
    """ % (message, env.deploy_version))

    
def migrate():
  virtualenv('cd web; python manage.py syncdb')
  virtualenv('cd web; python manage.py migrate')

def restart_webserver():
    "Restart the web server"
    sudo('apache2ctl restart')

