import pika
import json
import requests

class DownNode(object):

    def __init__(self, name, conf):
        self.__name = name
        self.__conf = conf

    def callback(self, ch, method, properties, body):
        msg = json.loads(body)
        print("Will download something")
        r = requests.get(msg['uri']) #TODO: use net
        # emit message to plugins
        if 'content-type' in r.headers.keys():
            ct = r.headers['content-type']
        elif 'Content-Type' in r.headers.keys():
            ct = r.headers['Content-Type']
        else:
            ct = ''
        if not ct.strip():
            pass #emit bad type
        if ';' in ct:
            ct = ct.split(';')[0]
        stub = {'url': r.url, 'type': ct, 'content': r.text}
        with pika.BlockingConnection(pika.ConnectionParameters(self.__conf.getProperty('rabbitHost', 'localhost'))) as connection:
            channel = connection.channel()
            channel.exchange_declare(exchange='process', type='fanout')
            channel.basic_publish(exchange='process', routing_key='', body=stub)
        ch.basic_ack(delivery_tag = method.delivery_tag)

    def start(self):
        with pika.BlockingConnection(pika.ConnectionParameters(self.__conf.getProperty('rabbitHost', 'localhost'))) as connection:
            channel = connection.channel()
            channe.queue_declare(queue='down', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(self.callback, queue='down')
            print("Network node " + self.__name + " waiting for messages")
            channel.start_consuming()
