from deploy import system
from os.path import join
from fabric.api import *

def set_current(release_name):
    new_release_path = join(env.releases_path, release_name)
    return system.symlink(new_release_path, env.current)

def releases(releases_path):
    return system.list_dirs(releases_path)

def current_release():
    return releases(env.releases_path)[-1]

def current_release_path():
    return join(env.releases_path, current_release())