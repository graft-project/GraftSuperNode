from decorators import store_job_result
from config import SEED_SAMPLE, API_URL
from queue_manager import QueueManager
from logger import service_logger
from defines import *
import requests
import time


def send_request(url, data):
    start = time.time()
    response = requests.post(url, json=data)
    print(time.time() - start)
    return response


def broadcast_job(callback_code, **kwargs):
    broadcast_message(callback_code, **kwargs)


@store_job_result
def broadcast_message(callback_code, **kwargs):
    seed_sample = kwargs.get('seed_sample')
    active_node = kwargs.get('active_node')
    result = True
    for node in seed_sample:
        if node != active_node:
            url = API_URL.format(node)
            response = send_request(url, kwargs).json()
            service_logger.debug(response)
            if response.get(RESULT_KEY) != STATUS_OK:
                result = False
                break
    res = {'callback_code': callback_code, 'result': result}
    return res


class GraftBroadcastAPI(object):
    def __init__(self):
        self._active_node = None
        self._seed_sample = SEED_SAMPLE
        self._queue = QueueManager.instance()

    def register_supernode(self, address):
        self._active_node = address

    def add_sample_node(self, address):
        if not self._seed_sample.__contains__(address):
            self._seed_sample.append(address)

    def sample(self):
        return self._seed_sample

    def sale(self, **kwargs):
        kwargs.update({BROADCAST_KEY: self._active_node, CALL_KEY: BROADCAST_SALE})
        self.run_broadcast_job(callback=self._broadcast_callback, **kwargs)
        return True

    def _broadcast_callback(self, result):
        service_logger.debug(result)

    def pay(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_PAY})
        self.run_broadcast_job(callback=self._broadcast_callback, **kwargs)
        return True

    def pay_request(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_PAY_REQUEST})
        self.run_broadcast_job(callback=self._broadcast_callback, **kwargs)
        return True

    def approval(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_APPROVAL})
        self.run_broadcast_job(callback=self._broadcast_callback, **kwargs)
        return True

    def transaction(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_TRANSACTION})
        self.run_broadcast_job(callback=self._broadcast_callback, **kwargs)
        return True

    def run_broadcast_job(self, callback, **kwargs):
        kwargs.update({'seed_sample': self._seed_sample, 'active_node': self._active_node})
        self._queue.run_job(broadcast_job, callback=callback, **kwargs)

    @staticmethod
    def _send_request(url, data):
        start = time.time()
        response = requests.post(url, json=data)
        print(time.time() - start)
        return response
