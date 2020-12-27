#!/usr//bin/env python3

import logging
from colorlog import ColoredFormatter

import hackimposition
from hackimposition import ImposerPageTemplate, ImposerAlgo, impose
from hackimposition.options import processArgs
import PyPDF2
import sys

stream = logging.StreamHandler()
LF = "%(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
stream.setFormatter(ColoredFormatter(LF))
logger = logging.getLogger(hackimposition.__name__).addHandler(stream)

def main():
    hackimposition.impose(*processArgs(sys.argv[1:]))

    """
    loglevel = "DEBUG"
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logger.setLevel(level=numeric_level)

    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')
    """


if __name__ == '__main__':
    main()
