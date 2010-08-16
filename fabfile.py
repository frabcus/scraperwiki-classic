import getpass

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

def www():
    "The main www server (horsell)"
    env.hosts = ['89.16.177.212:7822']
    env.path = '/var/www/scraperwiki'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.virtualhost_path = "/"
    env.deploy_version = "www"

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
    return run(temp + env.activate + '&&' + command)


def buildout():
    virtualenv('buildout')

def write_changeset():
    try:
        env.changeset = virtualenv('hg log | egrep -m 1 -o "[a-zA-Z0-9]*$"')
        virtualenv("echo %s > web/changeset.txt" % env.changeset)
    except:
        env.changeset = ""

def update_revision():
    """
    Put the current HG revision in a file so that Django can use it to avoid caching JS files
    """
    virtualenv("hg identify | awk '{print $1}' > web/revision.txt")

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
    env.kforge_user = raw_input('Your kforge Username: ')
    kforge_pass = pw = getpass.getpass('Your kforge Password: ')
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')

    run("""cd %s; 
        hg pull https://%s:%s@kforgehosting.com/scraperwiki/hg; 
        hg update -C %s""" % (env.path,
                              env.kforge_user,
                              kforge_pass,
                              env.branch))
    
    migrate()
    write_changeset()
    install_cron()
    create_tarball()
    update_revision()
    restart_webserver()   
    email(message)

def email(message_body=None):
    if not message_body:
        print "Please Enter your deploy message: \r"
        message_body = raw_input()
    
    message = """From: ScraperWiki <mercurial@scraperwiki.com>
Subject: New Scraperwiki Deployment to %(version)s (deployed by %(user)s)

%(user)s deployed changeset %(changeset)s, with the following comment:

%(message_body)s

""" % {
        'version' : env.deploy_version,
        'user' : env.kforge_user,
        'changeset' : env.changeset,
        'message_body' : message_body,
        }
    sudo("""echo "%s" | sendmail scrapewiki-commits@googlegroups.com """ % message)
    
def migrate():
    virtualenv('cd web; python manage.py syncdb')
    virtualenv('cd web; python manage.py migrate')

def restart_webserver():
    "Restart the web server"
    sudo('apache2ctl restart')

def create_tarball():
    virtualenv("mkdir -p ./web/media/src/; hg archive -t tgz ./web/media/src/scraperwiki.tar.gz")
