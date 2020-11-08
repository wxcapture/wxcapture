#!/usr/bin/env python3
"""Ensure goesrecv is running"""


# import libraries
import os
import subprocess
from subprocess import Popen, PIPE
import wxcutils


def is_running(process_name):
    """see if a process is running"""
    try:
        cmd = subprocess.Popen(('ps', '-A'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('grep', process_name), stdin=cmd.stdout)
        cmd.wait()
        MY_LOGGER.debug('output = %s', output)
        if process_name in output.decode('utf-8'):
            MY_LOGGER.debug('%s is running', process_name)
            return True
    except:
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return False


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
CONFIG_PATH = CODE_PATH + 'config/'

# start logging
MODULE = 'watchdog'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')
MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('CODE_PATH = %s', CODE_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('OUTPUT_PATH = %s', OUTPUT_PATH)
MY_LOGGER.debug('IMAGE_PATH = %s', IMAGE_PATH)
MY_LOGGER.debug('WORKING_PATH = %s', WORKING_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# test if goesproc is running
if not is_running('goesrecv'):
    # need to kick off the code
    MY_LOGGER.debug('Kicking it off')
    wxcutils.run_cmd('/home/pi/gk-2a/goestools/build/src/goesrecv/goesrecv -i 1 -c /home/pi/gk-2a/goesrecv.conf &')
    if is_running('goesrecv'):
        MY_LOGGER.debug('goesrecv is now running')
    else:
        MY_LOGGER.critical('goesrecv is NOT running and could not be restarted')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
