from storages.local_data_storage import LocalDataStorage
from storages.redis_data_storage import RedisDataStorage
from graft_broadcast_api import GraftBroadcastAPI
from config import REDIS_HOST, REDIS_PORT, STORAGE_TYPE, LOCAL_STORAGE, REDIS_STORAGE
from threading import Lock
from defines import *


class SupernodeProtocol:
    TRANSACTION_CACHE_LEVEL = "transaction_cache"
    TRANSACTION_STATUS_LEVEL = "transaction_status"
    AUTHORIZATION_CACHE_LEVEL = "authorization_cache"

    _instance = None
    _lock = Lock()

    def __init__(self):
        self._broadcast_api = GraftBroadcastAPI()
        init_storage = {LOCAL_STORAGE: self._init_local_storage,
                        REDIS_STORAGE: self._init_redis_storage}
        if init_storage.get(STORAGE_TYPE, None) is None:
            raise ValueError
        init_storage.get(STORAGE_TYPE)()
        self._requests = {
            # Wallet DAPI
            'ReadyToPay': self.ready_to_pay,
            'RejectPay': self.reject_pay,
            'Pay': self.pay,
            'GetPayStatus': self.get_pay_status,
            # Point of Sale DAPI
            'Sale': self.sale,
            'RejectSale': self.reject_sale,
            'GetSaleStatus': self.get_sale_status,
            # Broadcast DAPI
            'BroadcastAccountLock': self.broadcast_account_lock,
            'BroadcastTransaction': self.broadcast_transaction,
            'BroadcastRemoveAccountLock': self.broadcast_remove_account_lock,
            # Generic DAPI
            'GetWalletBalance': self.get_wallet_balance
        }

    def register_supernode(self, address):
        self._broadcast_api.register_supernode(address)

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = SupernodeProtocol()
        return cls._instance

    def process(self, **kwargs):
        call = kwargs[CALL_KEY]
        del kwargs[CALL_KEY]
        call_func = self._requests.get(call)
        if call_func is not None:
            return call_func(**kwargs)
        return None

    # Wallet DAPI

    def ready_to_pay(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        key_image = kwargs.get(KEY_IMAGE_KEY, None)
        if pid is None or key_image is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS, TRANSACTION_KEY: None}
        if not self._trans_cache_storage.exists(pid):
            return {RESULT_KEY: ERROR_PAYMENT_ID_DOES_NOT_EXISTS, TRANSACTION_KEY: None}
        # TODO: How to determine account
        if self._auth_cache_storage.exists(pid) and self._auth_cache_storage.get_data(pid) == key_image:
            return {RESULT_KEY: ERROR_ACCOUNT_LOCKED, TRANSACTION_KEY: None}
        # TODO: send BroadcastAccountLock()
        print(self._trans_cache_storage.get_data(pid))
        return {RESULT_KEY: STATUS_OK, TRANSACTION_KEY: self._trans_cache_storage.get_data(pid)}

    def reject_pay(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        if pid is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS}
        if not self._trans_cache_storage.exists(pid):
            return {RESULT_KEY: ERROR_PAYMENT_ID_DOES_NOT_EXISTS}
        self._trans_cache_storage.delete_data(pid)
        self._trans_status_storage.store_data(pid, STATUS_REJECTED)
        # TODO: send BroadcastRemoveAccountLock()
        return {RESULT_KEY: STATUS_OK}

    def pay(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        transaction = kwargs.get(TRANSACTION_KEY, None)
        if pid is None or transaction is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS}
        # TODO: Validates
        # TODO: start Mining
        # TODO: send BroadcastTransaction()
        self._trans_status_storage.store_data(pid, STATUS_APPROVED)
        return {RESULT_KEY: STATUS_OK}

    def get_pay_status(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        if pid is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS, PAY_STATUS_KEY: STATUS_NONE}
        if not self._trans_status_storage.exists(pid):
            return {RESULT_KEY: ERROR_PAYMENT_ID_DOES_NOT_EXISTS, PAY_STATUS_KEY: STATUS_NONE}
        return {RESULT_KEY: STATUS_OK, PAY_STATUS_KEY: self._trans_status_storage.get_data(pid)}

    # Point of Sale DAPI

    def sale(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        transaction = kwargs.get(TRANSACTION_KEY, None)
        broadcast_node = kwargs.get(BROADCAST_KEY, None)
        if broadcast_node is None:
            if pid is None or transaction is None:
                return {RESULT_KEY: ERROR_EMPTY_PARAMS}
            if self._trans_cache_storage.exists(pid):
                return {RESULT_KEY: ERROR_PAYMENT_ID_ALREADY_EXISTS}
        if not self._trans_cache_storage.exists(pid):
            self._trans_cache_storage.store_data(pid, transaction)
            self._trans_status_storage.store_data(pid, STATUS_PROCESSING)
        result = {RESULT_KEY: STATUS_OK}
        if broadcast_node is None:
            if not self._broadcast_api.sale(**kwargs):
                result = {RESULT_KEY: ERROR_BROADCAST_FAILED}
        else:
            self._broadcast_api.add_sample_node(broadcast_node)
        return result

    def reject_sale(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        if pid is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS}
        if not self._trans_cache_storage.exists(pid):
            return {RESULT_KEY: ERROR_PAYMENT_ID_DOES_NOT_EXISTS}
        self._trans_cache_storage.delete_data(pid)
        self._trans_status_storage.store_data(pid, STATUS_REJECTED)
        return {RESULT_KEY: STATUS_OK}

    def get_sale_status(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        if pid is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS, SALE_STATUS_KEY: STATUS_NONE}
        if not self._trans_status_storage.exists(pid):
            return {RESULT_KEY: ERROR_PAYMENT_ID_DOES_NOT_EXISTS, SALE_STATUS_KEY: STATUS_NONE}
        return {RESULT_KEY: STATUS_OK, SALE_STATUS_KEY: self._trans_status_storage.get_data(pid)}

    # Broadcast DAPI

    def broadcast_account_lock(self, **kwargs):
        return None

    def broadcast_transaction(self, **kwargs):
        pid = kwargs.get(PID_KEY, None)
        transaction = kwargs.get(TRANSACTION_KEY, None)
        approvals = kwargs.get(APPROVALS_KEY, None)
        if pid is None or transaction is None or approvals is None:
            return {RESULT_KEY: ERROR_EMPTY_PARAMS}
        if not self._trans_cache_storage.exists(pid):
            return {RESULT_KEY: ERROR_PAYMENT_ID_DOES_NOT_EXISTS}
        self._trans_cache_storage.delete_data(pid)
        self._trans_status_storage.store_data(pid, STATUS_APPROVED)
        return {RESULT_KEY: STATUS_OK}

    def broadcast_remove_account_lock(self, **kwargs):
        return None

    # Generic DAPI

    def get_wallet_balance(self, **kwargs):
        return None

    def get_supernode_list(self, **kwargs):
        return None

    def get_sample(self, **kwargs):
        return None

    def broadcast_supernode_add(self, **kwargs):
        return None

    def supernode_healthcheck(self, **kwargs):
        return None

    def broadcast_supernode_remove(self, **kwargs):
        return None

    def _init_local_storage(self):
        self._trans_cache_storage = LocalDataStorage(self.TRANSACTION_CACHE_LEVEL)
        self._trans_status_storage = LocalDataStorage(self.TRANSACTION_STATUS_LEVEL)
        self._auth_cache_storage = LocalDataStorage(self.AUTHORIZATION_CACHE_LEVEL)

    def _init_redis_storage(self):
        self._trans_cache_storage = RedisDataStorage(REDIS_HOST, REDIS_PORT, self.TRANSACTION_CACHE_LEVEL)
        self._trans_status_storage = RedisDataStorage(REDIS_HOST, REDIS_PORT, self.TRANSACTION_STATUS_LEVEL)
        self._auth_cache_storage = RedisDataStorage(REDIS_HOST, REDIS_PORT, self.AUTHORIZATION_CACHE_LEVEL)
