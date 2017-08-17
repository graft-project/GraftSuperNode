from data_storage import DataStorage
from threading import Lock


class LocalDataStorage(DataStorage):
    def __init__(self, level):
        self._storage = {}
        DataStorage.__init__(self, level)

    def get_data(self, pid):
        return self._storage.get(pid)

    def store_data(self, pid, data):
        self._storage[pid] = data

    def delete_data(self, pid):
        del self._storage[pid]

    def exists(self, pid):
        return self._storage.__contains__(pid)
