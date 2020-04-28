#!/usr/bin/env python3
"""Run pactl and QSSTV
Needs to be run from VNC and left running
Otherwise receive_sstv.py will not be able
to decode sstv images"""

import os
import sys
import time
from subprocess import Popen, PIPE
import wxcutils

# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
CONFIG_PATH = CODE_PATH + 'config/'

HOME = os.environ['HOME']
HOME = '/home/pi/'
FILE_PATH = HOME + '/wxcapture/process/'

# start logging
MODULE = 'qsstv'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')

try:
    MY_LOGGER.debug('wait 10 seconds to allow background processes to start')
    time.sleep(10)

    MY_LOGGER.debug('start pactl')
    CMD = Popen(['/usr/bin/pactl', 'load-module', 'module-null-sink', 'sink_name=virtual-cable']
                , stdout=PIPE, stderr=PIPE)
    STDOUT, STDERR = CMD.communicate()
    MY_LOGGER.debug('stdout:%s', STDOUT)
    MY_LOGGER.debug('stderr:%s', STDERR)

    MY_LOGGER.debug('wait 5 seconds to allow pactl to start')
    time.sleep(5)

    MY_LOGGER.debug('start qsstv')
    CMD = Popen(['qsstv'], stdout=PIPE, stderr=PIPE)
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
