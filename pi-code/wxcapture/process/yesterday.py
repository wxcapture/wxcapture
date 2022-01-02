#!/usr/bin/env python3

import os
import time
import calendar
from datetime import datetime
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

# start logging
MODULE = 'yesterday'
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


MY_LOGGER.debug('Loading the current day passes')
PASSES = wxcutils.load_json(WORKING_PATH, 'passes_today.json')

MY_LOGGER.debug('Saving raw yesterday file')
wxcutils.save_json(WORKING_PATH, 'passes_yesterday.json', PASSES)

TIME_NOW = int(time.time())
MY_LOGGER.debug('Epoch time now = %d', TIME_NOW)

# need to find all the PM passes in the last 10 hours
# since this is running at midnight
MAX_AGE = 10 * 60 * 60
MY_LOGGER.debug('Finding all passes in the last 10 hours')
PREVIOUS = []
for sat_pass in PASSES:
    pass_age = TIME_NOW - int(sat_pass['time'])
    MY_LOGGER.debug('Pass epoch time = %d, age = %d (sec) [%f hours]', int(sat_pass['time']), pass_age, pass_age / 3600)
    if pass_age < MAX_AGE:
        MY_LOGGER.debug('Including this pass')
        PREVIOUS.append(sat_pass)
    else:
        MY_LOGGER.debug('Excluding this pass')

MY_LOGGER.debug('Saving PM passes for yesterday file')
wxcutils.save_json(WORKING_PATH, 'passes_pm_yesterday.json', PREVIOUS)


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
