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
        layout_directories(branch)
        return fn(branch, *args, **kwargs)
    return wrapper


def setup_env_for(branch):
    env.branch = branch
    env.github_user = 'smn'
    env.github_repo_name = 'richmond'
    env.github_repo = 'http://github.com/%(github_user)s/%(github_repo_name)s.git' % env
    
    env.deploy_to = '/var/praekelt/richmond/%(branch)s' % env
    env.releases_path = "%(deploy_to)s/releases" % env
    env.current = "%(deploy_to)s/current" % env
    env.shared_path = "%(deploy_to)s/shared" % env
    env.tmp_path = "%(shared_path)s/tmp" % env
    env.pip_cache_path = "%(tmp_path)s/cache/pip" % env
    env.pids_path = "%(tmp_path)s/pids" % env
    env.logs_path = "%(shared_path)s/logs" % env
    env.repo_path = "%(shared_path)s/repositories" % env
    env.layout = [
        env.releases_path,
        env.tmp_path,
        env.pip_cache_path,
        env.pids_path,
        env.logs_path,
        env.repo_path
    ]

def repo_path(repo_name):
    return '%(repo_path)s/%(github_repo_name)s' % env

def repo(repo_name):
    """helper to quickly switch to a repository"""
    return cd(repo_path(repo_name))

def layout_directories(branch):
    require('hosts')
    setup_env_for(branch)
    require('layout', provided_by=['setup_env_for'])
    system.create_dirs(env.layout)

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
    # /var/praekelt/richmond/staging/releases/20100603_125848
    new_release_path = join(env.releases_path, new_release_name)
    # /var/praekelt/richmond/staging/releases/20100603_125848/richmond
    # Django needs the project name as it's parent dir since that is 
    # automagically appended to the loadpath
    new_release_repo = join(new_release_path, env.github_repo_name)
    
    system.create_dir(new_release_path)
    system.copy_dirs(repo_path(env.github_repo_name), new_release_path)
    setup_virtualenv(branch)
    # ensure we're deploying the exact revision as we locally have
    base.set_current(new_release_name)


@setup_env
def execute(branch, command, release=None):
    release = release or base.current_release()
    directory = join(env.releases_path, release, env.github_repo_name)
    virtualenv(directory, command)

@setup_env
def setup_virtualenv(branch):
    with cd(join(base.current_release_path(), env.github_repo_name)):
        return run(" && ".join([
            "virtualenv --no-site-packages ve",
            "source ve/bin/activate",
            "pip -E ve install --download-cache=%(pip_cache_path)s -r config/requirements.pip" % env,
            "python setup.py install",
        ]))


def virtualenv(directory, command, env_name='ve'):
    activate = 'source %s/bin/activate' % env_name
    deactivate = 'deactivate'
    with cd(directory):
        run(' && '.join([activate, command, deactivate]))


@setup_env
def update(branch):
    current_release = base.releases(env.releases_path)[-1]
    with cd(join(base.current_release_path(), env.github_repo_name)):
        git.pull(branch)


@setup_env
def start_webapp(branch, **kwargs):
    virtualenv(
        join(base.current_release_path(), env.github_repo_name),
        twistd.start_command('richmond_webapp', **kwargs)
    )

@setup_env
def restart_webapp(branch, **kwargs):
    virtualenv(
        join(base.current_release_path(), env.github_repo_name),
        twistd.restart_command('richmond_webapp', **kwargs)
    )

@setup_env
def stop_webapp(branch, **kwargs):
    virtualenv(
        join(base.current_release_path(), env.github_repo_name),
        twistd.stop_command('richmond_webapp', **kwargs)
    )

@setup_env
def releases(branch):
    releases = base.releases(env.releases_path)
    print "%(host)s - %(releases_path)s" % env
    for release in releases:
        print "\t: %s" % release

    