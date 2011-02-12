import getpass

from fabric.api import *

# globals
PROJECT_NAME = 'ScraperWiki'

# environments
def dev():
    "On the scraperwiki server, accessible from http://dev.scraperwiki.com"
    env.hosts = ['dev.scraperwiki.com']
    env.path = '/var/www/scraperwiki'
    env.branch = 'default'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.deploy_version = "dev"
    env.webserver = True

def www():
    "The main www server (horsell)"
    env.hosts = ['89.16.177.212:7822']
    env.path = '/var/www/scraperwiki'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.deploy_version = "www"
    env.webserver = True

def umls():
    "The UML server (rush)"
    env.hosts = ['89.16.177.195:7822']
    env.path = '/var/www/scraperwiki'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.deploy_version = "umls"
    env.webserver = False

def datastore():
    "The datastore server (burbage)"
    env.hosts = ['89.16.177.176:7822']
    env.path = '/var/www/scraperwiki'
    env.branch = 'stable'
    env.web_path = 'file:///home/scraperwiki/scraperwiki'
    env.activate = env.path + '/bin/activate'
    env.user = 'scraperdeploy'
    env.deploy_version = "datastore"
    env.webserver = False

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
    virtualenv('buildout -N')

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
    run('crontab %s/cron/crontab.%s' % (env.path, env.deploy_version))
    sudo('crontab %s/cron/crontab-root.%s' % (env.path, env.deploy_version))

def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """

    print "***************** DEPLOY *****************"
    print "Please Enter your deploy message: \r"
    message = raw_input()
    env.name = raw_input('Your name: ')
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
    email(message, old_revision, new_revision)

    print "Deploy successful"
    print "Old revision = %s" % old_revision
    print "New revision = %s" % new_revision

def email(message_body=None, old_revision=None, new_revision=None):
    if not message_body:
        print "Please Enter your deploy message: \r"
        message_body = raw_input()
    
    message = """From: ScraperWiki <mercurial@scraperwiki.com>
Subject: New Scraperwiki Deployment to %(version)s (deployed by %(user)s)

%(user)s deployed changeset %(changeset)s, with the following comment:

%(message_body)s

Old revision: %(old_revision)s
New revision: %(new_revision)s

""" % {
        'version' : env.deploy_version,
        'user' : env.name,
        'changeset' : env.changeset,
        'message_body' : message_body,
        'old_revision': old_revision,
        'new_revision': new_revision,
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

def test():
    if env.deploy_version != "dev":
        print "Testing can only be done on the dev machine"
    else:
        virtualenv('cd web; python manage.py test')
