from graft_node_tools import get_wallet_rpc_credentials
from config import GRAFT_NODE_URL, GRAFT_NODE_ADDRESS
from requests.auth import HTTPDigestAuth
from decorators import store_job_result
from queue_manager import QueueManager
from logger import service_logger
from defines import *
import requests
import time


def send_request(url, data, username=None, password=None):
    start = time.time()
    if username is not None and password is not None:
        response = requests.post(url, json=data, auth=HTTPDigestAuth(username, password))
    else:
        service_logger.info("create post")
        response = requests.post(url, json=data)
    print(time.time() - start)
    return response


def node_job(callback_code, **kwargs):
    node_message(callback_code, **kwargs)


@store_job_result
def node_message(callback_code, **kwargs):
    message = kwargs['message']
    service_logger.info(message)
    service_logger.info(type(message))
    service_logger.info(type(message['params']))
    pid = kwargs['pid']
    rpc_login = kwargs['rpc_login']
    rpc_pass = kwargs['rpc_pass']
    url = GRAFT_NODE_URL.format(GRAFT_NODE_ADDRESS)
    response = send_request(url, message, rpc_login, rpc_pass)
    service_logger.debug(response)
    result = {'status': 'error', 'status_code': response.status_code,
              'request': message, 'pid': pid}
    if response.status_code == 200:
        response = response.json()
        service_logger.info(response)
        if response.__contains__('error'):
            result.update({'details': response['error']})
        else:
            r = response.get('result', {})
            if len(r.keys()) == 0:
                r.update({'result': True})
            result.update({'status': 'result', 'details': r})
    res = {'callback_code': callback_code, 'result': result}
    return res


class GraftNodeAPI(object):
    def __init__(self, login=None, password=None):
        self._rpc_login = login
        self._rpc_pass = password
        if self._rpc_login is None or self._rpc_pass is None:
            credentials = get_wallet_rpc_credentials()
            if credentials is not None:
                self._rpc_login = credentials[0]
                self._rpc_pass = credentials[1]
        self._queue = QueueManager.instance()

    def get_data(self, pid, message):
        return {
            'message': message,
            'pid': pid,
            'rpc_login': self._rpc_login,
            'rpc_pass': self._rpc_pass
        }

    @staticmethod
    def rpc_request(method, params=None):
        rpc = {
            "jsonrpc": "2.0",
            "id": "0",
            "method": method
        }
        if params is not None:
            rpc.update({"params": params})
        return rpc

    def getbalance(self, callback, **kwargs):
        raise NotImplementedError

    def getaddress(self, callback, **kwargs):
        raise NotImplementedError

    def getheight(self, callback, **kwargs):
        raise NotImplementedError

    def transfer(self, callback, **kwargs):
        raise NotImplementedError

    def transfer_split(self, callback, **kwargs):
        raise NotImplementedError

    def sweep_dust(self, callback, **kwargs):
        raise NotImplementedError

    def sweep_all(self, callback, **kwargs):
        raise NotImplementedError

    def store(self, callback, **kwargs):
        raise NotImplementedError

    def get_payments(self, callback, **kwargs):
        raise NotImplementedError

    def get_bulk_payments(self, callback, **kwargs):
        raise NotImplementedError

    def get_transfers(self, callback, **kwargs):
        raise NotImplementedError

    def get_transfer_by_txid(self, callback, **kwargs):
        raise NotImplementedError

    def incoming_transfers(self, callback, **kwargs):
        raise NotImplementedError

    def query_key(self, callback, **kwargs):
        raise NotImplementedError

    def make_integrated_address(self, callback, **kwargs):
        raise NotImplementedError

    def split_integrated_address(self, callback, **kwargs):
        raise NotImplementedError

    def stop_wallet(self, callback, **kwargs):
        data = self.get_data(kwargs[GRAFT_NODE_PID], self.rpc_request("close_wallet"))
        self.run_node_job(callback=callback, **data)
        return True

    def make_uri(self, callback, **kwargs):
        raise NotImplementedError

    def parse_uri(self, callback, **kwargs):
        raise NotImplementedError

    def rescan_blockchain(self, callback, **kwargs):
        raise NotImplementedError

    def set_tx_notes(self, callback, **kwargs):
        raise NotImplementedError

    def get_tx_notes(self, callback, **kwargs):
        raise NotImplementedError

    def sign(self, callback, **kwargs):
        raise NotImplementedError

    def verify(self, callback, **kwargs):
        raise NotImplementedError

    def export_key_images(self, callback, **kwargs):
        raise NotImplementedError

    def import_key_images(self, callback, **kwargs):
        raise NotImplementedError

    def get_address_book(self, callback, **kwargs):
        raise NotImplementedError

    def add_address_book(self, callback, **kwargs):
        raise NotImplementedError

    def delete_address_book(self, callback, **kwargs):
        raise NotImplementedError

    def rescan_spent(self, callback, **kwargs):
        raise NotImplementedError

    def start_mining(self, callback, **kwargs):
        raise NotImplementedError

    def stop_mining(self, callback, **kwargs):
        raise NotImplementedError

    def get_languages(self, callback, **kwargs):
        raise NotImplementedError

    def create_wallet(self, callback, **kwargs):
        print(kwargs[GRAFT_NODE_PID])
        params = {
            GRAFT_NODE_FILENAME: kwargs[GRAFT_NODE_FILENAME],
            GRAFT_NODE_PASSWORD: kwargs[GRAFT_NODE_PASSWORD],
            GRAFT_NODE_LANGUAGE: "English"
        }
        data = self.get_data(kwargs[GRAFT_NODE_PID], self.rpc_request("create_wallet", params))
        self.run_node_job(callback=callback, **data)
        return True

    def open_wallet(self, callback, **kwargs):
        print(kwargs[GRAFT_NODE_PID])
        params = {
            GRAFT_NODE_FILENAME: kwargs[GRAFT_NODE_FILENAME],
            GRAFT_NODE_PASSWORD: kwargs[GRAFT_NODE_PASSWORD],
        }
        data = self.get_data(kwargs[GRAFT_NODE_PID], self.rpc_request("open_wallet", params))
        self.run_node_job(callback=callback, **data)
        return True

    def run_node_job(self, callback, **kwargs):
        self._queue.run_job(node_job, callback=callback, **kwargs)

    @staticmethod
    def _send_request(url, data):
        start = time.time()
        response = requests.post(url, json=data)
        print(time.time() - start)
        return response
