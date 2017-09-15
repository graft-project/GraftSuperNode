from storages.rq_redis_data_storage import RQRedisDataStorage
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
    message = kwargs.get('message')
    if is_expired(message):
        return {'callback_code': callback_code, 'result': 'expired'}
    result = True
    for node in seed_sample:
        url = API_URL.format(node)
        response = send_request(url, message)
        service_logger.debug(response)
        if response.status_code == 200:
            response = response.json()
            if response.get(RESULT_KEY) != STATUS_OK:
                result = False
                break
        else:
            result = False
            break
    res = {'callback_code': callback_code, 'result': result}
    return res


def is_expired(message):
    message_temp_key = TEMPORAL_KEY_FORMAT % (message.get(CALL_KEY),
                                              message.get(PID_KEY))
    expired_list = list(RQRedisDataStorage.instance().get_data(REDIS_EXPIRED_JOBS_KEY, []))
    if expired_list.__contains__(message_temp_key):
        expired_list.remove(message_temp_key)
        RQRedisDataStorage.instance().store_data(REDIS_EXPIRED_JOBS_KEY, expired_list)
        return True
    return False


class GraftBroadcastAPI(object):
    def __init__(self):
        self._active_node = None
        self._seed_sample = SEED_SAMPLE
        self._queue = QueueManager.instance()

    def register_supernode(self, address):
        self._active_node = address

    def active_node(self):
        return self._active_node

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
        seed_sample = self._seed_sample[:]
        # seed_sample.remove(self._active_node)
        job_data = {'message': kwargs, 'seed_sample': seed_sample}
        self._queue.run_job(broadcast_job, callback=callback, **job_data)

    @staticmethod
    def _send_request(url, data):
        start = time.time()
        response = requests.post(url, json=data)
        print(time.time() - start)
        return response
