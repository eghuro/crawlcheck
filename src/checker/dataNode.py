#!/usr/bin/env python3
import pika
import json

class DataNode(object):

    def __init__(self, name, conf, api):
        self.__name = name
        self.__conf = conf
        self.__api = api

    def callback(self, ch, method, properties, body):
        msg = json.loads(body)
        if msg['operation'] == 'link':
            self.__api.log_link(msg['parent'], msg['uri'], msg['new'])
        elif msg['operation'] == 'defect':
            if 'severity' in msg:
                severity = msg['severity']
            else:
                severity = 0.5
            self.__api.log_defect(msg['tid'], msg['name'], msg['additional'], msg['evidence'], severity)
        elif msg['operation'] == 'cookie':
            self.__api.log_cookie(msg['tid'], msg['name'], msg['value'])
        else:
            print("Unsupported operation %s" % msg['operation'])
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def start(self):
        with pika.BlockingConnection(pika.ConnectionParameters(self.__conf.getProperty('rabbitHost', 'localhost'))) as connection:
                channel = connection.channel()
                channel.queue_declare(queue='db', durable=True)
                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(self.callback, queue='db')
                print("Data node " + self.__name + " waiting for messages")
                channel.start_consuming()
