from defines import REDIS_GENERAL_CHANNEL, REDIS_JOB_RESULT_KEY
from storages.rq_redis_data_storage import RQRedisDataStorage
from redis_subscriber import RedisSubscriber
from config import REDIS_HOST, REDIS_PORT
from redis.client import StrictRedis
from logger import worker_logger
from threading import Lock
from hashlib import sha1
from os import urandom
from rq import Queue
import ast
import re


class QueueManager:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self._queue = Queue(connection=StrictRedis(host=REDIS_HOST, port=REDIS_PORT))
        self._rq_redis_storage = RQRedisDataStorage.instance()
        self._redis_subscriber = RedisSubscriber.instance()
        self._subscribed_callbacks = {}
        self._listen_for_results()

    @classmethod
    def instance(cls):
        """
            Synchronized method which creates (if required) and returns
            current instance of WorkerInterface
        :return: WorkerInterface instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = QueueManager()
        return cls._instance

    def run_job(self, job_to_run, callback=None, **kwargs):
        """
            Adds job to worker's queue so it will be picked up by worker.

        :param job_to_run: Job that will be placed inside queue
        :param callback: optional callback function that will be executed after job is finished.
        :param kwargs: Arguments to run the job with.
        """
        worker_logger.info('Running job - %s' % job_to_run)
        if callback is not None:
            callback_code = sha1(urandom(32)).hexdigest()
            self._subscribed_callbacks.update({callback_code: callback})
            kwargs.update({'callback_code': callback_code})
        self._queue.enqueue(job_to_run, **kwargs)

    def _listen_for_results(self):
        """
            Initializes redis changes listener for given key pattern.

        """
        self._redis_subscriber.subscribe(channel_key=REDIS_GENERAL_CHANNEL % '*', callback=self._process_results)

    def _process_results(self, message):
        """
            Parses redis changes message and processes the result.

        :param message: Redis changes message.
        """
        if message.kind == 'pmessage':
            if message.body == 'set':
                job_result_key = re.search('.*:(%s)' % (REDIS_JOB_RESULT_KEY % ('.*', '.*')), message.channel).group(1)
                callback_code = re.search('.*:%s' % (REDIS_JOB_RESULT_KEY % ('(.*):.*', '.*')), message.channel).group(
                    1)
                callback, result = self._parse_result_get_callback(result_key=job_result_key,
                                                                   callback_code=callback_code)

                self._run_results_callback(result=result, result_key=job_result_key, callback=callback,
                                           callback_code=callback_code)

    def _parse_result_get_callback(self, result_key, callback_code, algo_result=False):
        result = self._rq_redis_storage.get_data(result_key)
        worker_logger.debug('Raw result - %s' % result)
        try:
            result = ast.literal_eval(result) if result is not None else {}
        except ValueError as e:
            worker_logger.exception(msg=str(e))
            result = {}
        if algo_result:
            result = result.get('result', False)
        worker_logger.debug('Result dictionary - %s' % result)

        callback = self._subscribed_callbacks.get(callback_code)
        return callback, result

    def _run_results_callback(self, result, result_key, callback, callback_code):
        try:
            worker_logger.debug('Running callback with result - %s' % result)
            worker_logger.debug('Callback - %s' % callback)
            callback(result)
        except Exception as e:
            worker_logger.warning(msg=str(e))
        finally:
            self._rq_redis_storage.delete_data(result_key)
            try:
                del self._subscribed_callbacks[callback_code]
            except KeyError as e:
                worker_logger.warning(e)

    def queue_jobs_count(self):
        """
            Returns number of jobs that are currently inside the worker's queue

        :return: int number of queue jobs.
        """
        return self._queue.count

    def get_all_jobs_from_queue(self):
        """
            Returns list of jobs that are currently inside the worker's queue

        :return: list of queue jobs.
        """
        return self._queue.get_jobs()

    def clear_queue(self):
        """
            Clears worker's queue. It deletes everything that is inside the queue.

        """
        self._queue.empty()
