class DataStorage:
    def __init__(self, level):
        self._level = level

    def storage_level(self):
        return self._level

    def get_data(self, pid, default=None):
        raise NotImplementedError

    def store_data(self, pid, data):
        raise NotImplementedError

    def delete_data(self, pid):
        raise NotImplementedError

    def exists(self, pid):
        raise NotImplementedError
