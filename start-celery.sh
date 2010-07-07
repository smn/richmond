#!/bin/bash
# Poor man's daemonizing of celeryd
source ./ve/bin/activate && \
    ./manage.py celeryd \
        --settings=$1 \
        --logfile=./logs/celeryd.$1.$2.log \
        --loglevel=debug \
        --concurrency=1 && \
    deactivate