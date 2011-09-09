import getpass

# TODO:
# Use "local" to run Django tests automatically
# Use "local" to run Selenium tests.

from fabric.api import *

# globals
PROJECT_NAME = 'ScraperWiki'

# These are taken from and named after our puppet classes.
# We should move to using them for fab deployment.
# env.roledefs = {
#    'webserver': ['rush', 'yelland']
#    'datastore': ['burbage', 'kippax']
#    'vm': ['horsell', 'kippax'],

#    'refine': ['burbage', '']
#    'sandbox': ['burbage', '']
#    'muninserver': ['rush', '']
#    'backup': ['kippax', '']
#}

###########################################################################
# Server configurations

# If git+git fails then sudo easy_install pip==0.8.2
# environments
@task
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

@task
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

@task
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

@task
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

###########################################################################
# Helpers

def run_in_virtualenv(command):
    temp = 'cd %s; source ' % env.path
    return run(temp + env.activate + '&&' + command)

def email(old_revision=None, new_revision=None):
    message = """From: ScraperWiki <developers@scraperwiki.com>
Subject: New Scraperwiki Deployment to %(cron_version)s (deployed by %(user)s)

%(user)s deployed changeset %(changeset)s

Old revision: %(old_revision)s
New revision: %(new_revision)s

""" % {
        'cron_version' : env.cron_version,
        'user' : env.name,
        'changeset' : env.changeset,
        'old_revision': old_revision,
        'new_revision': new_revision,
        }
    sudo("""echo "%s" | sendmail deploy@scraperwiki.com """ % message)
 ###########################################################################
# Tasks

@task
def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """

    sudo('hg clone file:///home/scraperwiki/scraperwiki %(path)s' % env)        
    sudo('chown -R %(fab_user)s %(path)s' % env)
    sudo('cd %(path)s; easy_install virtualenv' % env)
    run('hg clone %(web_path)s %(path)s' % env, fail='ignore')
    run('cd %(path)s; virtualenv --no-site-packages .' % env)
    run_in_virtualenv('easy_install pip')

    deploy()

@task
def run_puppet():
    """
    Runs the puppetd on the specific machine
    """
    sudo("puppetd --no-daemonize --onetime --debug")        
    
def buildout():
    run_in_virtualenv('buildout -N -q')

def update_js_cache_revision():
    """
    Put the current HG revision in a file so that Django can use it to avoid caching JS files
    """
    run_in_virtualenv("hg identify | awk '{print $1}' > web/revision.txt")

def install_cron():
    run('crontab %(path)s/cron/crontab.%(cron_version)s' % env)
    sudo('crontab %(path)s/cron/crontab-root.%(cron_version)s' % env)

@task
def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """

    env.name = getpass.getuser()
    import time

    with cd(env.path):
        old_revision = run("hg identify")
        run("hg pull; hg update -C %(branch)s" % env)
        new_revision = run("hg identify" % env)
    
    if env.webserver:
        buildout()
        migrate()
        update_js_cache_revision()
        restart_webserver()   

    install_cron()

    if env.email_deploy:
        email(old_revision, new_revision)

    print "Deploy successful"
    print "Old revision = %s" % old_revision
    print "New revision = %s" % new_revision

   
def migrate():
    run_in_virtualenv('cd web; python manage.py syncdb')
    run_in_virtualenv('cd web; python manage.py migrate')

def restart_webserver():
    "Restart the web server"
    sudo('apache2ctl graceful')

@task
def test():
    if env.host != "dev.scraperwiki.com":
        print "Testing can only be done on the dev machine"
    else:
        run_in_virtualenv('cd web; python manage.py test')


