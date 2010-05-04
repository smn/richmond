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
    $ rabbitmqctl -n rabbit@localhost set_permissions -p /richmond richmond '.*' '.*' '.*'
    Setting permissions for user "richmond" in vhost "richmond" ...
    ...done.
    
That last line gives the user 'richmond' on virtual host 'richmond' configure, read & write access to all resources that match those three regular expressions. Which, in this case, matches all resources in the vhost.

Run the twisted plugin like so:

    $ export PYTHONPATH=`pwd`/ve/src/python-ssmi/src
    $ twistd -n amqp

For some reason I had to specify the PYTHONPATH manually, not sure if I'm doing stuff wrong or if `virtualenv` & `pip` are failing on me.

Remove the `-n` option to daemonize the application.