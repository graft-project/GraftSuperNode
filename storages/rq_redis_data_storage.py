from redis_data_storage import RedisDataStorage
from config import REDIS_HOST, REDIS_PORT
from defines import REDIS_JOB_RESULT_KEY
from threading import Lock


class RQRedisDataStorage(RedisDataStorage):
    _instance = None
    _lock = Lock()

    def __init__(self):
        RedisDataStorage.__init__(self, REDIS_HOST, REDIS_PORT, 'RQRedisQueue')

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = RQRedisDataStorage()
        return cls._instance

    def store_job_result(self, record_dict, callback_code):
        job_result_key = REDIS_JOB_RESULT_KEY & callback_code
        self._storage.set(name=job_result_key, value=record_dict)
