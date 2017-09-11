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
        return self.broadcast_message(**kwargs)

    def pay(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_PAY})
        return self.broadcast_message(**kwargs)

    def approval(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_APPROVAL})
        return self.broadcast_message(**kwargs)

    def transaction(self, **kwargs):
        kwargs.update({CALL_KEY: BROADCAST_TRANSACTION})
        return self.broadcast_message(**kwargs)

    def broadcast_message(self, **kwargs):
        result = True
        for node in self._seed_sample:
            if node != self._active_node:
                url = API_URL.format(node)
                response = self._send_request(url, kwargs).json()
                print response
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
