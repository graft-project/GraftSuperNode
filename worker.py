from config import REDIS_HOST, REDIS_PORT
from rq_gevent_worker import GeventWorker
from redis.client import StrictRedis
from rq import Connection, Queue
from logger import worker_logger


if __name__ == '__main__':
    # Tell rq what Redis connection to use
    with Connection(connection=StrictRedis(host=REDIS_HOST, port=REDIS_PORT)):
        q = Queue(connection=StrictRedis(host=REDIS_HOST, port=REDIS_PORT))
        waiting_jobs = q.get_jobs()
        for job in waiting_jobs:
            q.remove(job)
        gevent_worker = GeventWorker(q)
        gevent_worker.log = worker_logger
        gevent_worker.work()
