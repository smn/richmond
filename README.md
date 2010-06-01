Richmond
========

PubSub platform for connecting online messaging services such as SMS and USSD to a horizontally scalable backend of workers.

If you're wondering about the name. Apparently Richmond has is a great city for commuters, few traffic problems. Seemed like a good name for a high-traffic message bus application.

Getting started
---------------

Make sure you have your AMQP broker running. I've only tested it with RabbitMQ, in theory, it should work with any other AMQP 0.8 spec based broker.

    $ rabbitmq-server

RabbitMQ will automatically assign a node name for you. For my network that doesn't work too well because the rest of the clients are unable to connect. If you run into the same problem, try the following:

    $ RABBITMQ_NODENAME=rabbit@localhost rabbitmq-server

Make sure you have configured your login credentials & virtual host stuff in RabbitMQ. This is the minimal stuff for this to work 'out of the box':

    $ rabbitmqctl -n rabbit@localhost add_user richmond richmond
    Creating user "richmond" ...
    ...done.
    $ rabbitmqctl -n rabbit@localhost add_vhost /richmond
    Creating vhost "richmond" ...
    ...done.
    $ rabbitmqctl -n rabbit@localhost set_permissions -p /richmond richmond \
        '.*' '.*' '.*'
    Setting permissions for user "richmond" in vhost "richmond" ...
    ...done.
 
That last line gives the user 'richmond' on virtual host 'richmond' configure, read & write access to all resources that match those three regular expressions. Which, in this case, matches all resources in the vhost.

This project uses [virtualenv][virtualenv] and [pip][pip] to to create a sandbox and manage the required libraries at the required versions. Make sure you have both installed.

Setup a virtual python environment in the directory `ve`. The `--no-site-packages` makes sure that all required dependencies are installed your the virtual environments `site-packages` directory even if they exist in Python's global `site-packages` directory.

    $ virtualenv --no-site-packages ./ve/ 

Start the environment by sourcing `activate`. This'll prepend the name of the virtual environment to your shell prompt, informing you that the prompt is still active.

        $ source ve/bin/activate

When you're done run `deactivate` to exit the virtual environment.

Install the required libraries with pip into the virtual environment. They're pulled in from both [pypi][pypi] and [GitHub][github]. Make sure you have the development package for python (python-dev or python-devel or something of that sort) installed, Twisted needs it when it's being built.

    $ pip -E ./ve/ install -r config/requirements.pip
 
Running Richmond
----------------

Richmond is implemented using a [Pub/Sub][pubsub] design using the [Competing Consumer pattern][competing consumers]. 

Richmond is started as a `richmond_service` plugin for Twisted.

Every Richmond services connects to RabbitMQ and allows for both consuming and publishing of messages. Richmond allows for connecting incoming and outoing messages to a backend of workers.

Richmond currently has a TruTeq service that allows for receiving and sending of USSD messages over TruTeq's SSMI protocol. The TruTeq service connects to the SSMI service and connects to RabbitMQ. It publishes all incoming messages over SSMI as JSON to the receive queue in RabbitMQ and it publishes all incoming messages over the send queue back to TruTeq over SSMI.

The worker reads all incoming JSON objects on the receive queue and publishes a response back to the send queue for the TruTeq service to publish over SSMI.

Make sure you update the configuration file in `config/truteq.cfg` and start the broker:

    $ source ve/bin/activate
    (ve)$ twistd --pidfile=tmp/pids/twistd.richmond.truteq.service.pid -n \     
        richmond_service \
        --service=richmond.services.truteq.service.USSDService \
        --config=config/truteq.cfg
    ...
 
    $ source ve/bin/activate
    (ve)$ twistd --pidfile=tmp/pids/twistd.richmond.truteq.worker.1.pid -n \
        richmond_service \
        --service richmond.campaigns.vumi.VumiUSSDWorker \
        --config=config/truteq.cfg
    ...

The worker's --service/-s option allows you to specify a class that subclasses `richmond.services.base.RichmondService`.

Remove the `-n` option to have `twistd` run in the background. The `--pidfile` option isn't necessary, `twistd` will use 'twistd.pid' by default. However, since we could have multiple brokers and workers running at the same time on the same machine it is good to be explicit since `twistd` will assume an instance is already running if 'twistd.pid' already exists.

Creating a custom worker
------------------------

We'll create a worker that responds to USSD json objects. We'll subclass the `richmond.services.worker.PubSubWorker`. Workers should always start a queue consumer and a queue publisher. For our example it should start a publisher for publishing outgoing USSD messages to the TruTeq service and it should start a consumer for receiving incoming USSD messages from the TruTeq service.

A basic TruTeq consumer is provided and it provides the following functions.
They're called for each of the relevant messages that arrive over the queue.

    * new_ussd_session(msisdn, message)
    * existing_ussd_session(msisdn, message)
    * timed_out_ussd_session(msisdn, message)
    * end_ussd_session(msisdn, message)

This is what the code for a consumer for TruTeq would look like:

    from richmond.services.truteq.base import Publisher, Consumer, SessionType
    from richmond.services.worker import PubSubWorker
    from twisted.python import log

    class EchoConsumer(Consumer):
    
        def new_ussd_session(self, msisdn, message):
            self.reply(msisdn, "Hello, this is an echo service for " \
                                "testing. Reply with whatever. Reply '0' " \
                                "to end session.", 
                                SessionType.existing)
    
        def existing_ussd_session(self, msisdn, message):
            if message == "0":
                self.reply(msisdn, "quitting, goodbye!", SessionType.end)
            else:
                self.reply(msisdn, message, SessionType.existing)
    
        def timed_out_ussd_session(self, msisdn, message):
            log.msg('%s timed out, removing client' % msisdn)
    
        def end_ussd_session(self, msisdn, message):
            log.msg('%s ended the session, removing client' % msisdn)
    
    
    
    class USSDWorker(PubSubWorker):
        consumer_class = EchoConsumer
        publisher_class = Publisher
    

Start the worker:

    $ source ve/bin/activate
    (ve)$ twistd --pidfile=tmp/pids/twistd.richmond.truteq.worker.2.pid -n \
        richmond_service \
        --service=richmond.campaigns.example.USSDWorker
        --config=config/truteq.conf
    ...


Running the Webapp / API
------------------------

The webapp is a regular Django application. Before you start make sure the `DATABASE` settings in `src/richmond/webapp/settings.py` are up to date. `Richmond` is being developed with `PostgreSQL` as the default backend for the Django ORM but this isn't a requirement.

For development start it within the virtual environment:

    $ source ve/bin/activate
    (ve)$ python setup.py develop
    (ve)$ ./manage.py syncdb
    (ve)$ ./manage.py runserver
    ...

For development it sometimes is handy to have Celery run in eager mode. In eager mode, tasks avoids the queue entirely and are processed immediately in the main process. Do this by settings the environment variable 'RICHMOND_SKIP_QUEUE'

    (ve)$ RICHMOND_SKIP_QUEUE=True ./manage.py runserver

This is specified in the `settings.py` file, if so desired, you can also default it to `DEBUG` so that when `DEBUG=True` the queue will always be skipped.

When running in production start it with the `twistd` plugin `richmond_webapp`
 
    $ source ve/bin/activate
    (ve)$ twistd --pidfile=tmp/pids/richmond.webapp.pid -n richmond_webapp

Run the tests for the webapp API with `./manage.py` as well:

    $ source ve/bin/activate
    (ve)$ ./manage.py test api

Scheduling SMS for delivery via the API
---------------------------------------

The API is HTTP with concepts borrowed from REST. All URLs have a rate limit of 60 hits per 60 seconds and require HTTP Basic Authentication.

There are currently two transports available. [Clickatell][clickatell] or [Opera][opera]. The API for both is exactly the same, just replace '/clickatell/' for '/opera/' in the URL.

Sending via Clickatell:

    http://localhost:8000/api/v1/sms/clickatell/send.json

Sending via Opera:

    http://localhost:8000/api/v1/sms/opera/send.json


**Sending SMSs**

    $ curl -u 'username:password' -X POST \
    >   http://localhost:8000/api/v1/sms/clickatell/send.json \
    >   -d 'to_msisdn=27123456789' \
    >   -d 'from_msisdn=27123456789' \
    >   -d 'message=hello world'
    [
        {
            "delivered_at": "2010-05-13 11:34:34", 
            "id": 5, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456789", 
            "transport_status": 0, 
            "message": "hello world"
        }
    ]

**Sending Batched SMSs**

Sending multiple SMSs is as simple as sending a simple SMS. Just specify multiple values for `to_msisdn`.

    $ curl -u 'username:password' -X POST \
    >   http://localhost:8000/api/v1/sms/clickatell/send.json \
    >   -d 'to_msisdn=27123456780' \
    >   -d 'to_msisdn=27123456781' \
    >   -d 'to_msisdn=27123456782' \
    >   -d 'from_msisdn=27123456789' \
    >   -d 'message=hello world'
    [
        {
            "delivered_at": "2010-05-13 11:32:22", 
            "id": 2, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456780", 
            "transport_status": 0, 
            "message": "hello world"
        }, 
        {
            "delivered_at": "2010-05-13 11:32:22", 
            "id": 3, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456781", 
            "transport_status": 0, 
            "message": "hello world"
        }, 
        {
            "delivered_at": "2010-05-13 11:32:22", 
            "id": 4, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456782", 
            "transport_status": 0, 
            "message": "hello world"
        }
    ]

**Sending Personalized SMSs**

Personalized SMSs can be sent by specifying a template and the accompanying variables.

All template variables should be prefixed with 'template_'. In the template you can refer to the values without their prefix.

    $ curl -u 'username:password' -X POST \
    > http://localhost:8000/api/v1/sms/clickatell/template_send.json \
    > -d 'to_msisdn=27123456789' \
    > -d 'to_msisdn=27123456789' \
    > -d 'to_msisdn=27123456789' \
    > -d 'from_msisdn=27123456789' \
    > -d 'template_name=Simon' \
    > -d 'template_surname=de Haan' \
    > -d 'template_name=Jack' \
    > -d 'template_surname=Jill' \
    > -d 'template_name=Foo' \
    > -d 'template_surname=Bar' \
    > -d 'template=Hello {{name}} {{surname}}'
    [
        {
            "delivered_at": "2010-05-14 04:42:09", 
            "id": 6, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456789", 
            "transport_status": 0, 
            "message": "Hello Foo Bar"
        }, 
        {
            "delivered_at": "2010-05-14 04:42:09", 
            "id": 7, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456789", 
            "transport_status": 0, 
            "message": "Hello Jack Jill"
        }, 
        {
            "delivered_at": "2010-05-14 04:42:09", 
            "id": 8, 
            "from_msisdn": "27123456789", 
            "to_msisdn": "27123456789", 
            "transport_status": 0, 
            "message": "Hello Simon de Haan"
        }
    ]

Checking the status of sent SMSs
--------------------------------

Once an SMS has been scheduled for sending you can check it's status via the API. There are 3 options of retrieving previously sent SMSs.

**Retrieving one specific SMS**

    $ curl -u 'username:password' -X GET \
    > http://localhost:8000/api/v1/sms/clickatell/status/1.json \
    {
        "delivered_at": null, 
        "created_at": "2010-05-14 16:31:01", 
        "updated_at": "2010-05-14 16:31:01", 
        "transport_status_display": "", 
        "from_msisdn": "27123456789", 
        "id": 1, 
        "to_msisdn": "27123456789", 
        "message": "testing api", 
        "transport_status": 0
    }

**Retrieving SMSs sent since a specific date**

    $ curl -u 'username:password' -X GET \
    > http://localhost:8000/api/v1/sms/clickatell/status.json?since=2009-01-01
    [
        {
            "delivered_at": null, 
            "created_at": "2010-05-14 16:31:01", 
            "updated_at": "2010-05-14 16:31:01", 
            "transport_status_display": "", 
            "from_msisdn": "27123456789", 
            "id": 51, 
            "to_msisdn": "27123456789", 
            "message": "testing api", 
            "transport_status": 0
        }, 
        ...
        ...
        ...
    ]

**Retrieving SMSs by specifying their IDs**

    $ curl -u 'username:password' -X GET \
    > "http://localhost:8000/api/v1/sms/clickatell/status.json?id=3&id=4"
    [
        {
            "delivered_at": null, 
            "created_at": "2010-05-14 16:31:01", 
            "updated_at": "2010-05-14 16:31:01", 
            "transport_status_display": "", 
            "from_msisdn": "27123456789", 
            "id": 4, 
            "to_msisdn": "27123456789", 
            "message": "testing api", 
            "transport_status": 0
        }, 
        {
            "delivered_at": null, 
            "created_at": "2010-05-14 16:31:01", 
            "updated_at": "2010-05-14 16:31:01", 
            "transport_status_display": "", 
            "from_msisdn": "27123456789", 
            "id": 3, 
            "to_msisdn": "27123456789", 
            "message": "testing api", 
            "transport_status": 0
        }
    ]
    
Specifying Callbacks
--------------------

There are two types of callbacks defined. These are `sms_received` and `sms_receipt`. Each trigger an HTTP POST to the given URLs.

    $ curl -u 'username:password' -X PUT \
    > http://localhost:8000/api/v1/account/callbacks.json \
    > -d 'sms_received=http://localhost/sms/clickatell/received/callback' \
    > -d 'sms_receipt=http://localhost/sms/clickatell/receipt/callback'
    [
        {
            "url": "http://localhost/sms/clickatell/received/callback", 
            "created_at": "2010-05-14 16:50:13", 
            "name": "sms_received", 
            "updated_at": "2010-05-14 16:50:13"
        }, 
        {
            "url": "http://localhost/sms/clickatell/receipt/callback", 
            "created_at": "2010-05-14 16:50:13", 
            "name": "sms_receipt", 
            "updated_at": "2010-05-14 16:50:13"
        }
    ]

The next time an SMS is received or a SMS receipt is delivered, Richmond will post the data to the URLs specified.

Accepting delivery receipts from the transports
-----------------------------------------------

Both [Clickatell][clickatell] and [Opera][opera] support notification of an SMS being delivered. In the general configuration areas of both sites there is an option where a URL callback can be specified. Clickatell or Opera will then post the delivery report to that URL.

Richmond will accept delivery reports from both:

For [Clickatell][clickatell]:

    http://localhost:8000/api/v1/sms/clickatell/receipt.json

For [Opera][opera]:

    http://localhost:8000/api/v1/sms/opera/receipt.json

Accepting inbound SMS from the transports
-----------------------------------------

Like the SMS delivery reports, both [Opera][opera] and [Clickatell][clickatell] will forward incoming SMSs to Richmond. 

For Clickatell the URL is:

    http://localhost:8000/api/v1/sms/clickatell/receive.json

For Opera the URL is:

    http://localhost:8000/api/v1/sms/opera/receive.xml

Note the XML suffix on the URL. The resource returns XML whereas Clickatell returns JSON. This is important! Opera can forward our response to further callbacks in their application and it needs to be formatted as XML for upstream callbacks to make sense of it.

Webapp Workers
--------------

Richmond uses [Celery][celery], the distributed task queue. The main Django process only registers when an SMS is received,sent or when a delivery report is received. The real work is done by the Celery workers.

Start the Celery worker via `manage.py`:

    (ve)$ ./manage.py celeryd
    
For a complete listing of the command line options available, use the help command:

    (ve)$ ./manage.py help celeryd


[virtualenv]: http://pypi.python.org/pypi/virtualenv
[pip]: http://pypi.python.org/pypi/pip
[pypi]: http://pypi.python.org/pypi/
[GitHub]: http://www.github.com/
[pubsub]: http://en.wikipedia.org/wiki/Publish/subscribe
[competing consumers]: http://www.eaipatterns.com/CompetingConsumers.html
[celery]: http://ask.github.com/celery
[clickatell]: http://clickatell.com
[opera]: http://operainteractive.co.za/