from storages.rq_redis_data_storage import RQRedisDataStorage


def store_job_result(fn):
    def wrapped(callback_code, **kwargs):
        res = fn(callback_code, **kwargs)
        RQRedisDataStorage.instance().store_job_result(record_dict=res, callback_code=callback_code)
        return None
    return wrapped
