"""
1. create directory layout
2. check of we have a repo
    yes? -> pull in latest updates
    no? -> clone
4. deploy
    1. pull in latest repo updates from branch
    2. copy latest revision to release dir
    3. checkout given commit
5. restart
    1. 

"""
from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from datetime import datetime
from os.path import join

from deploy import git, system, base, twistd

RELEASE_NAME_FORMAT = '%Y%m%d_%H%M%S' # timestamped
# default for now
env.hosts = ['ubuntu-server.local']

def setup_env(fn):
    def wrapper(branch, *args, **kwargs):
        require('hosts')
        setup_env_for(branch)
        require('layout', provided_by=['setup_env_for'])
        system.create_dirs(env.layout)
        return fn(branch, *args, **kwargs)
    return wrapper

def setup_env_for(branch):
    env.branch = branch
    env.github_user = 'smn'
    env.github_repo_name = 'richmond'
    env.github_repo = 'http://github.com/%(github_user)s/%(github_repo_name)s.git' % env
    
    env.deploy_to = '/var/praekelt/vumi/%(branch)s' % env
    env.releases_path = "%(deploy_to)s/releases" % env
    env.current = "%(deploy_to)s/current" % env
    env.shared_path = "%(deploy_to)s/shared" % env
    env.tmp_path = "%(shared_path)s/tmp" % env
    env.pids_path = "%(tmp_path)s/pids" % env
    env.logs_path = "%(shared_path)s/logs" % env
    env.repo_path = "%(shared_path)s/repositories" % env
    env.layout = [
        env.releases_path,
        env.tmp_path,
        env.pids_path,
        env.logs_path,
        env.repo_path
    ]

def repo_path(repo_name):
    return '%(repo_path)s/%(github_repo_name)s' % env

def repo(repo_name):
    """helper to quickly switch to a repository"""
    return cd(repo_path(repo_name))

@setup_env
def deploy(branch):
    if not git.is_repository(repo_path(env.github_repo_name)):
        # repository doesn't exist, do a fresh clone
        with cd(env.repo_path):
            git.clone(env.github_repo, env.github_repo_name)
        with repo(env.github_repo_name):
            git.checkout(branch)
    else:
        # repository exists
        with repo(env.github_repo_name):
            if not (branch == git.current_branch()):
                # switch to our branch if not already
                git.checkout(branch)
            # pull in the latest code
            git.pull(branch)
    # 20100603_125848
    new_release_name = datetime.utcnow().strftime(RELEASE_NAME_FORMAT)
    # /var/praekelt/vumi/staging/releases/20100603_125848
    new_release_path = join(env.releases_path, new_release_name)
    # /var/praekelt/vumi/staging/releases/20100603_125848/richmond
    # Django needs the project name as it's parent dir since that is 
    # automagically appended to the loadpath
    new_release_repo = join(new_release_path, env.github_repo_name)
    
    system.create_dir(new_release_path)
    system.copy_dirs(repo_path(env.github_repo_name), new_release_path)
    setup_virtual_env(new_release_path)
    # ensure we're deploying the exact revision as we locally have
    base.set_current(new_release_name)


@setup_env
def virtualenv(branch):
    with cd(join(base.current_release_path(), env.github_repo_name)):
        return run(" && ".join([
            "virtualenv --no-site-packages ve",
            "source ve/bin/activate",
            "pip -E ve install -r config/requirements.pip" % env,
            "python setup.py install",
        ]))

def _enter_virtualenv():
    with cd(join(base.current_release(), env.github_repo_name)):
        run('source ve/bin/activate')

def _exit_virtualenv():
    run('deactivate')

@setup_env
def update(branch):
    current_release = base.releases(env.releases_path)[-1]
    with cd(join(env.releases_path, current_release, env.github_repo_name)):
        git.pull(branch)


@setup_env
def start(branch):
    _enter_virtualenv()
    with cd(base.current_release_path()):
        twistd.start('richmond_webapp')
    _exit_virtualenv()

@setup_env
def stop(branch):
    with cd(base.current_release_path()):
        twistd.stop('richmond_webapp')

@setup_env
def releases(branch):
    releases = base.releases(env.releases_path)
    print "%(host)s - %(releases_path)s" % env
    for release in releases:
        print "\t: %s" % release

    