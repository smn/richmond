from twisted.internet import defer
from twisted.python import log
from twisted.python.log import logging

@defer.inlineCallbacks
def open_channel(client, channel_id):
    """
    Open a channel for the given client with the given channel id. The
    channel_id's should be integers. Not sure why, some txamqp magic.
    """
    log.msg("Opening channel with id %s" % channel_id, logLevel=logging.DEBUG)
    channel = yield client.channel(channel_id)
    yield channel.channel_open()
    log.msg("Channel %s opened" % channel_id, logLevel=logging.DEBUG)
    defer.returnValue(channel)


@defer.inlineCallbacks
def join_queue(client, channel, exchange_name, exchange_type, queue_name, 
                routing_key, durable=False):
    log.msg("Joining queue '%s' with routing key '%s'" % 
                            (queue_name, routing_key), logLevel=logging.DEBUG)
    yield channel.queue_declare(queue=queue_name, durable=durable)
    log.msg("Declared queue %s, durable?: %s" % (queue_name, durable), 
                                                    logLevel=logging.DEBUG)
    yield channel.exchange_declare(exchange=exchange_name, 
                                        type=exchange_type,
                                        durable=durable)
    log.msg("Connected to exchange '%s' of type '%s'" % 
                                                (exchange_name, exchange_type),
                                                logLevel=logging.DEBUG)
    yield channel.queue_bind(queue=queue_name, exchange=exchange_name, 
                                routing_key=routing_key)
    log.msg("Bound '%s' to exchange '%s' with routing key '%s'" % 
                                (queue_name, exchange_name, routing_key), 
                                logLevel=logging.DEBUG)
    
    reply = yield channel.basic_consume(queue=queue_name)
    log.msg("Registered the consumer for queue '%s'" % queue_name, 
                                                logLevel=logging.DEBUG)
    queue = yield client.queue(reply.consumer_tag)
    defer.returnValue(queue)


