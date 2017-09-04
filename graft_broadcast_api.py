from config import SEED_SAMPLE, API_URL
from defines import *
import requests
import time


class GraftBroadcastAPI(object):
    def __init__(self):
        self._active_node = None
        self._seed_sample = SEED_SAMPLE

    def register_supernode(self, address):
        self._active_node = address

    def add_sample_node(self, address):
        if not self._seed_sample.__contains__(address):
            self._seed_sample.append(address)

    def sample(self):
        return self._seed_sample

    def sale(self, **kwargs):
        kwargs.update({BROADCAST_KEY: self._active_node, CALL_KEY: BROADCAST_SALE})
        result = True
        for node in self._seed_sample:
            url = API_URL.format(node)
            response = self._send_request(url, kwargs)
            if response.get(RESULT_KEY) != STATUS_OK:
                result = False
                break
        return result

    @staticmethod
    def _send_request(url, data):
        start = time.time()
        response = requests.post(url, json=data)
        print(time.time() - start)
        return response
