#!/usr//bin/env python3
""" main """

import logging
import sys
from colorlog import ColoredFormatter

import hackimposition
from hackimposition.options import process_args


stream = logging.StreamHandler()
LF = "%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
stream.setFormatter(ColoredFormatter(LF))
logger = logging.getLogger(hackimposition.__name__).addHandler(stream)


def main():
    """ begin imposition """
    hackimposition.impose(*process_args(sys.argv[1:]))

    #    logger.debug('debug message')
    #    logger.info('info message')
    #    logger.warning('warn message')
    #    logger.error('error message')
    #    logger.critical('critical message')



if __name__ == '__main__':
    main()
