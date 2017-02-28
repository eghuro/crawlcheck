#!/usr/bin/env python3
import pika
import json

class PluginNode(object):

    def __init__(self, name, plugin, conf):
        self.__name = name
        self.__plugin = plugin
        self.__conf = conf

    def callback(self, ch, method, properties, body):
        msg = json.loads(body)
        self.__plugin.check(msg['content'])

    def start(self):
        with pika.BlockingConnection(pika.ConnectionParameters(self.__conf.getProperty('rabbitHost', 'localhost'))) as connection:
            channel = connection.channel()
            channel.exchange_declare(exchange='process', type='fanout')
            result = channel.queue_declare(exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange='process', queue=queue_name)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(self.callback, queue=queue_name, no_ack=True)
            print("Plugin node " + self.__name + " waiting for messages")
            channel.start_consuming()
