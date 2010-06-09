# Twanalytics

Drinking from the twitter firehose & analyzing the data.

# Go go go!

* Make sure you have rabbitmq running
* Make sure you have CouchDB running at `http://localhost:5984/`
* Create & enter the virtualenv with 
    `virtualenv --no-site-packages ./ve && source ve/bin/activate`
* Install the requirements `pip install -r config/requirements.pip`
* Create a twitter database in CouchDB 
    `curl -X PUT http://localhost:5984/twitter`
* Install the CouchDB map/reduce stuff `couchapp push twanalytics/ twitter`
* Create `config/twitter.conf` and enter the following data:    

        [service]
        username: twitter username
        password: twitter password
        terms: words you want to track space delimited

* Start the Twitter service with:

        twistd --pidfile=tmp/pids/twitter.service.pid -n \
            richmond_service \
            -s richmond.services.twitter.service.TwitterService \
            -c config/twitter.conf

* Start the Twitter worker with

        twistd --pidfile=tmp/pids/twitter.worker.1.pid -n \
            richmond_service \
            -s richmond.services.twitter.worker.TwitterWorker

* Check your data in CouchDB by going to the Twitter database in [Futon][futon] and check the results of the map/reduce queries under the 'views' [drop down menu][continent-africa]

[futon]: http://localhost:5984/_utils/database.html?twitter/_all_docs
[continent-africa]: http://localhost:5984/_utils/database.html?twitter/_design/twanalytics/_view/continent-africa
