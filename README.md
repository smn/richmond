Richmond
========

Connecting the python-ssmi client to AMQP to allow for backends to scale more easily. 

If you're wondering about the name. Apparently Richmond has is a great city for commuters, few traffic problems. Seemed like a good name for a high-traffic message bus application.

Getting started
---------------

run `source setup-vritualenv.source` to do the virtualenv hoopla and install the requirements from `requirements.pip`.

Run the twisted plugin like so:

    $ export PYTHONPATH=`pwd`/ve/src/python-ssmi/src
    $ twistd amqp

For some reason I had to specify the PYTHONPATH manually, not sure if I'm doing stuff wrong or if `virtualenv` & `pip` are failing on me.