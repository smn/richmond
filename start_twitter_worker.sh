#!/bin/bash
twistd -n --pidfile=tmp/pids/twitter.worker.pid richmond_service --service=richmond.services.twitter.worker.TwitterWorker --config=environments/twitter.conf
