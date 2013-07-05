# encoding=UTF-8
"""
@author ideawu@163.com
@link http://www.ideawu.net/
"""
import logging
import logging.config

logging.addLevelName(5, 'TRACE')
logging.addLevelName(30, 'WARN')
logging.addLevelName(50, 'FATAL')

logger = None


def init(config):
	logging.config.fileConfig(config)
	globals()['logger'] = logging.getLogger('root')

def trace(msg):
	log = globals()['logger'];
	log.log(5, msg);

def debug(msg):
	log = globals()['logger'];
	log.debug(msg);

def info(msg):
	log = globals()['logger'];
	log.info(msg);

def warn(msg):
	log = globals()['logger'];
	log.warn(msg);

def error(msg):
	log = globals()['logger'];
	log.error(msg);

def fatal(msg):
	log = globals()['logger'];
	log.critical(msg);


""" TODO: if file_exists
"""
init('log.conf')
