from data_storage import DataStorage
from redis.client import StrictRedis
from threading import Lock


class RedisDataStorage(DataStorage):
    def __init__(self, host, port, level):
        DataStorage.__init__(self, level)
        self._storage = StrictRedis(host=host, port=port)

    def get_key(self, pid):
        return "{}_{}".format(self.storage_level(), pid)

    def get_data(self, pid, default=None):
        result = self._storage.get(name=self.get_key(pid))
        if result is None:
            result = default
        return result

    def store_data(self, pid, data):
        self._storage.set(name=self.get_key(pid), value=data)

    def delete_data(self, pid):
        self._storage.delete(self.get_key(pid))

    def exists(self, pid):
        return self._storage.exists(self.get_key(pid))
