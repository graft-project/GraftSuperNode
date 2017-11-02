#!/usr/bin/env python
# import signal
from supernode_protocol import SupernodeProtocol
from logger import service_logger as logger
from tornado.concurrent import Future
from tornado import gen
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.gen
import json


settings = {
    'port': 8080
}


class APIHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        tornado.web.RequestHandler.__init__(self, application, request, **kwargs)
        SupernodeProtocol.instance().register_delayed_callback(self._delayed_answer)

    def _delayed_answer(self, result):
        if result is not None:
            logger.info('Delayed Answer')
            logger.info('Send message: {}'.format(result))
            self.write(json.dumps(result))

    def res1(self):
        fut = gen.Future()
        fut.set_result("test")
        return fut

    def res2(self):
        fut2 = gen.Future()
        fut2.set_result("test2")
        return fut2

    @gen.coroutine
    def process(self, request_body):
        return [self.res1(), self.res2()]

        # return [tornado.gen.Return(1), tornado.gen.Return(2)]#SupernodeProtocol.instance().process(**request_body)
        # yield 2#SupernodeProtocol.instance().last_result()

    @gen.coroutine
    def post(self, *args, **kwargs):
        request_body = json.loads(self.request.body)
        SupernodeProtocol.instance().register_supernode(self.request.headers['Host'])
        logger.info('Received message: {}'.format(request_body))
        result = yield self.process(request_body)
        logger.info(result)
        if result is not None:
            logger.info('Send message: {}'.format(result))
            self.write(json.dumps(result))


class HttpApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/api', APIHandler)
        ]
        tornado.web.Application.__init__(self, handlers)


def run_tornado():
    http_app = HttpApplication()
    http_server = tornado.httpserver.HTTPServer(http_app)
    logger.info('Running REST tornado server on port %s ...' % settings['port'])
    http_server.listen(settings['port'])

    # signal.signal(signal.SIGUSR1, ConnectionTimeoutHandler.instance().log_open_connections)

    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    # Run tornado application
    run_tornado()
