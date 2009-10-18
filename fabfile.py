# globals
config.project_name = 'project_name'

# environments
def dev():
    "Use the local virtual server"
    config.fab_hosts = ['82.109.74.166']
    config.path = '/var/www/scraperwiki'
    config.tools_path = '/Users/sym/Projects/scraperwiki/bootstrap'
    config.web_path = 'ssh://scraperwiki@scraperwiki/web'
    config.activate = config.path + '/bin/activate'
    config.fab_user = 'sym'
    config.virtualhost_path = "/"


def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """
    require('fab_hosts', provided_by=[local])
    require('path')
    run('hg clone $(tools_path) $(path)', fail='ignore')
    run('cd $(path); virtualenv2.6 --no-site-packages . ; source bin/activate')
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

    require('fab_hosts', provided_by=[local])
    require('path')
    import time
    config.release = time.strftime('%Y%m%d%H%M%S')
    
    run('cd $(path); hg pull; hg update -C')
    
    buildout()
    
    sudo("""
    echo "$(message)" | mail -s "New Scraperwiki Deployment" simon.roe@talusdesign.co.uk -- -f mercurial@scraperwiki.com
    """)

    # migrate()
    # restart_webserver()












