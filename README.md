Richmond
========

Connecting the python-ssmi client to AMQP to allow for backends to scale more easily. 

If you're wondering about the name. Apparently Richmond has is a great city for commuters, few traffic problems. Seemed like a good name for a high-traffic message bus application.

Getting started
---------------

run `source setup-vritualenv.source` to do the virtualenv hoopla and install the requirements from `requirements.pip`.

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

Install the required libraries with pip into the virtual environment. They're pull in from both [pypi][pypi] and [GitHub][github].

    $ pip -E ./ve/ install -r config/requirements.pip
    
Start the environment by sourcing `activate`. This'll prepend the name of the virtual environment to your shell prompt, informing you that the prompt is still active.

    $ source ve/bin/activate

When you're done run `deactivate` to exit the virtual environment.

Running Richmond
----------------

Richmond is implemented using a [Pub/Sub][pubsub] design using the [Competing Consumer pattern][competing consumers]. 

Richmond has two plugins for Twisted, `richmond_broker` and `richmond_worker`.

The broker connects to TruTeq's SSMI service and connects to RabbitMQ. It publishes all incoming messages over SSMI as JSON to the receive queue in RabbitMQ and it publishes all incoming messages over the send queue back to TruTeq over SSMI.

The worker reads all incoming JSON objects on the receive queue and publishes a response back to the send queue for the `richmond_worker` to publish over SSMI.

Make sure you update the configuration file in `config/richmond-broker.cfg` and start the broker:

    $ source ve/bin/activate
    (ve)$ twistd --pidfile=tmp/pids/twistd.richmond.broker.pid -n \     
        richmond_broker -c config/richmond-broker.cfg
    ...
    
Make sure you update the worker configuration in `config/richmond-worker.cfg` if the defaults aren't suitable and start a worker.

    $ source ve/bin/activate
    (ve)$ twistd --pidfile=tmp/pids/twistd.richmond.worker.1.pid -n \
        richmond_worker -w richmond.workers.ussd.EchoWorker
    ...

The worker's -w option allows you to specify a class that subclasses `richmond.workers.base.RichmondWorker`.

Remove the `-n` option to have `twistd` run in the background. The `--pidfile` option isn't necessary, `twistd` will use 'twistd.pid' by default. However, since we could have multiple brokers and workers running at the same time on the same machine it is good to be explicit since `twistd` will assume an instance is already running if 'twistd.pid' already exists.

Creating a custom worker
------------------------

We'll create a worker that responds to USSD json objects. We'll subclass the `richmond.workers.ussd.USSDWorker` which itself subclasses `richmond.workers.base.RichmondWorker`. The `USSDWorker` subclasses `RichmondWorker`'s `consume` method and maps these to the following methods:

    * new_ussd_session(msisdn, message)
    * existing_ussd_session(msisdn, message)
    * timed_out_ussd_session(msisdn, message)
    * end_ussd_session(msisdn, message)

The `USSDWorker` also provides a `reply(msisdn, message, type)` that publishes the message of the given type to the queue.

Here's [working example][foobarworker]:
    
    from richmond.workers.ussd import USSDWorker, SessionType
    from twisted.python import log
    
    class FooBarWorker(USSDWorker):
    
        def new_ussd_session(self, msisdn, message):
            """Respond to new sessions"""
            self.reply(msisdn, "foo?", SessionType.existing)
        
        def existing_ussd_session(self, msisdn, message):
            """Respond to returning sessions"""
            if message == "bar" or message == "0": # sorry android is silly
                # replying with type `SessionType.end` ends the session
                self.reply(msisdn, "Clever. Bye!", SessionType.end)
            else:
                # replying with type `SessionType.existing` keeps the session
                # open and prompts the user for input
                self.reply(msisdn, "Say bar ...", SessionType.existing)
        
        def timed_out_ussd_session(self, msisdn, message):
            """These timed out unfortunately"""
            log.msg("%s timed out" % msisdn)
        
        def end_ussd_session(self, msisdn, message):
            """These ended the session themselves"""
            log.msg("%s ended session" % msisdn)
    



    

[virtualenv]: http://pypi.python.org/pypi/virtualenv
[pip]: http://pypi.python.org/pypi/pip
[pypi]: http://pypi.python.org/pypi/
[GitHub]: http://www.github.com/
[pubsub]: http://en.wikipedia.org/wiki/Publish/subscribe
[competing consumers]: http://www.eaipatterns.com/CompetingConsumers.html
[foobarworker]: http://github.com/smn/richmond/blob/master/richmond/workers/example.py