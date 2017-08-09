from logging.handlers import TimedRotatingFileHandler
import logging
import os


APP_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_PATH = os.path.join(APP_ROOT, 'logs')
SERVICE_LOG_NAME = 'service.log'

if not os.path.exists(LOGS_PATH):
    os.mkdir(LOGS_PATH)

### Log levels ###
# log_level = 'ERROR'
# log_level = 'WARN'
# log_level = 'INFO'
log_level = 'DEBUG'


logging.basicConfig(
    format='[%(asctime)s - %(name)s - %(levelname)s] - %(message)s',
    level=log_level
)

log_formatter = logging.Formatter('[%(asctime)s - %(name)s - %(levelname)s] - %(message).250s')


service_logger = logging.getLogger('supernode')
service_logger.setLevel(log_level)

if os.environ.get('SUPERVISOR_ENABLED') is not None:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    service_logger.addHandler(console_handler)
else:
    service_file_handler = TimedRotatingFileHandler(filename=os.path.join(LOGS_PATH, SERVICE_LOG_NAME),
                                                    when='d', interval=7, backupCount=3)
    service_file_handler.setFormatter(log_formatter)
    service_logger.addHandler(service_file_handler)
