from fabric.api import *
from os.path import join

def start(plugin, *args, **kwargs):
    uuid = kwargs.pop('uuid', 1)
    args = ["-%s" % arg for arg in args]
    kwargs = ["--%s=%s" % (k,v) for k,v in kwargs.items()]
    return run("twistd " \
        "--pidfile=%(pid_file)s " \
        "--logfile=%(log_file)s " \
        "%(plugin)s " \
        "%(args)s " \
        "%(kwargs)s " % {
            'pid_file': join(env.pids_path, 'twistd.%s.%s.pid' % (plugin, uuid)),
            'log_file': join(env.logs_path, 'twistd.%s.%s.log' % (plugin, uuid)),
            'plugin': plugin,
            'args': ' '.join(args),
            'kwargs': ' '.join(kwargs)
    })

def stop(plugin, uuid=1):
    return run('kill -HUP `cat %s`' % 
                join(env.pids_path, 'twistd.%s.%s.pid' (plugin, uuid)))

def restart(plugin, *args, **kwargs):
    stop(plugin, uuid)
    start(plugin, *args, **kwargs)