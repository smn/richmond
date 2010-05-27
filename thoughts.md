In an ideal scenario we'd start Richmond as follows:

    $ twistd -n richmond --service=USSDService --worker=USSDWorker
    $ twistd -n richmond --service=SMSService --worker=SMSWorker
    $ twistd -n richmond --service=XMPPService --worker=XMPPWorker
    $ twistd -n richmond --service=TwitterService --worker=TwitterWorker

For this to work:

1.  We'd need to have the following always available from the richmond plugin:
    1.  AMQP broker
    2.  Easy consumer & publisher creation without any AMQP boilerplate
    3.  A generic worker class that can be subclassed without any AMQP 
        boilerplate
    
2.  The Richmond plugin would need to start services provided. Itself would 
    need to start an AMQPService as well as start the service specified with 
    `--service=`. Probably a twisted MultiService.