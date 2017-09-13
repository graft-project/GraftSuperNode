from logger import worker_logger
import re

import tornado.gen
import tornado.ioloop
from threading import Lock

from defines import REDIS_GENERAL_CHANNEL
from tornadoredis import Client
from config import REDIS_HOST, REDIS_PORT


class RedisSubscriber:
    _instance = None
    _lock = Lock()

    def __init__(self):
        worker_logger.info('Initialized Redis Subscriber instance')
        self._client = Client(host=REDIS_HOST, port=int(REDIS_PORT))
        self._subscribers = {}
        self._listen()

    def __del__(self):
        worker_logger.info('Redis Subscriber was successfully destroyed')

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = RedisSubscriber()
        return cls._instance

    def subscribe(self, channel_key, callback):
        worker_logger.info('Subscribing channel - %s , with the callback - %s' % (channel_key, callback.__name__))
        self._subscribers.update({channel_key: callback})

    def unsubscribe(self, channel_key):
        worker_logger.info("Unsubscribing from channel - %s" % channel_key)
        if channel_key in self._subscribers:
            del self._subscribers[channel_key]

    @tornado.gen.engine
    def _listen(self):
        self._client.connect()
        yield tornado.gen.Task(self._client.psubscribe, "__keyspace*:%s" % (REDIS_GENERAL_CHANNEL % '*'))
        self._client.listen(self._message_handler)

    def _message_handler(self, message):
        if message.kind == 'pmessage':
            channel_key = re.search(REDIS_GENERAL_CHANNEL % '(.*)', message.channel)
            channel_callbacks = []
            if channel_key is not None:
                channel_key = channel_key.group(0)
                if channel_key in self._subscribers:
                    channel_callbacks[0] = self._subscribers.get(channel_key)
                else:
                    for subscriber_channel_key in self._subscribers.keys():
                        re_channel_key = subscriber_channel_key.replace('*', '.*')
                        if re.match(re_channel_key, channel_key):
                            channel_callbacks.append(self._subscribers.get(subscriber_channel_key))
            if len(channel_callbacks):
                for channel_callback in channel_callbacks:
                    try:
                        tornado.ioloop.IOLoop.instance().call_later(callback=channel_callback, delay=0,
                                                                    message=message)
                    except Exception as e:
                        worker_logger.warn('Failed to run channel callback')
                        worker_logger.exception(e)
