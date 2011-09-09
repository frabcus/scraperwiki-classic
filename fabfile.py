import getpass

from fabric.api import *

# globals
PROJECT_NAME = 'ScraperWiki'

# If git+git fails then sudo easy_install pip==0.8.2
# environments
def dev():
    "On the scraperwiki server, accessible from http://dev.scraperwiki.com"
    env.hosts = ['dev.scraperwiki.com']
    env.path = '/var/www/scraperwiki'
    env.branch = 'default'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.cron_version = "dev"
    env.webserver = True
    env.email_deploy = False

def dev_services():
    "The UML and datastore server (burbage)"
    env.hosts = ['kippax.scraperwiki.com']
    env.path = '/var/www/scraperwiki'
    env.branch = 'default'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.cron_version = "umls"
    env.webserver = False
    env.email_deploy = "deploy@scraperwiki.com"

def live():
    "The main www server"
    env.hosts = ['scraperwiki.com:7822']
    env.path = '/var/www/scraperwiki'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.cron_version = "www"
    env.webserver = True
    env.email_deploy = "deploy@scraperwiki.com"

def live_services():
    "The UML and datastore server (burbage)"
    env.hosts = ['burbage.scraperwiki.com:7822']
    env.path = '/var/www/scraperwiki'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.cron_version = "umls"
    env.webserver = False
    env.email_deploy = "deploy@scraperwiki.com"

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

def runpuppet():
    """
    Runs the puppetd on the specific machine
    """
    sudo("puppetd --no-daemonize --onetime --debug")        
    
def virtualenv(command):
    temp = 'cd %s; source ' % env.path
    return run(temp + env.activate + '&&' + command)

def buildout():
    virtualenv('buildout -N -q')

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
    run('crontab %s/cron/crontab.%s' % (env.path, env.cron_version))
    sudo('crontab %s/cron/crontab-root.%s' % (env.path, env.cron_version))

def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """

    print "***************** DEPLOY *****************"
    if env.email_deploy:
        print "(Optional, hit return if it's just routine) Enter your deploy comment: \r"
        message = raw_input()

    env.name = getpass.getuser()
    import time
    env.release = time.strftime('%Y%m%d%H%M%S')

    old_revision = run("cd %s; hg identify" % env.path)

    run("cd %s; hg pull; hg update -C %s" % (env.path, env.branch))

    new_revision = run("cd %s; hg identify" % env.path)
    
    if env.webserver:
        buildout()
        migrate()
        create_tarball()
        update_revision()
        restart_webserver()   

    write_changeset()
    install_cron()
    if env.email_deploy:
        email(message, old_revision, new_revision)

    print "Deploy successful"
    print "Old revision = %s" % old_revision
    print "New revision = %s" % new_revision

def email(message_body=None, old_revision=None, new_revision=None):
    if not message_body:
        message_body = "(no deploy comment)"
    
    message = """From: ScraperWiki <developers@scraperwiki.com>
Subject: New Scraperwiki Deployment to %(cron_version)s (deployed by %(user)s)

%(user)s deployed changeset %(changeset)s, with the following comment:

%(message_body)s

Old revision: %(old_revision)s
New revision: %(new_revision)s

""" % {
        'cron_version' : env.cron_version,
        'user' : env.name,
        'changeset' : env.changeset,
        'message_body' : message_body,
        'old_revision': old_revision,
        'new_revision': new_revision,
        }
    sudo("""echo "%s" | sendmail deploy@scraperwiki.com """ % message)
    
def migrate():
    virtualenv('cd web; python manage.py syncdb')
    virtualenv('cd web; python manage.py migrate')

def restart_webserver():
    "Restart the web server"
    sudo('apache2ctl graceful')

def create_tarball():
    virtualenv("mkdir -p ./web/media/src/; hg archive -t tgz ./web/media/src/scraperwiki.tar.gz")

def test():
    if env.hosts != "dev.scraperwiki.com":
        print "Testing can only be done on the dev machine"
    else:
        virtualenv('cd web; python manage.py test')


