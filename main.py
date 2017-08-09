#!/usr/bin/env python
# import signal
from supernode_protocol import SupernodeProtocol
from logger import service_logger as logger
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
    def post(self, *args, **kwargs):
        request_body = json.loads(self.request.body)
        logger.info('Received message: {}'.format(request_body))
        result = SupernodeProtocol.instance().process(**request_body)
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
