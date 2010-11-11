#!/bin/bash
twistd -n --pidfile=tmp/pids/twitter.service.pid richmond_service --service=richmond.services.twitter.service.TwitterService --config=environments/twitter.conf