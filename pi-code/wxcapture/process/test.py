#!/usr/bin/env python3
"""test code"""


# import libraries
import os
import sys
import json
import glob
import random
from subprocess import Popen, PIPE
import wxcutils
import wxcutils_pi

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
MODULE = 'test'
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

try:

    IMAGE_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-NOAA.json')

    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')


    for tweet_group in IMAGE_OPTIONS['tweet groups']:
        for tweet_option in tweet_group:
            random_pick = random.randint(1, len(tweet_group[tweet_option])) - 1
            enhancement = tweet_group[tweet_option][random_pick]['type']
            tweet_text = tweet_group[tweet_option][random_pick]['text'].replace('[LOCATION]', CONFIG_INFO['Location']) 
            MY_LOGGER.debug('enahancement = %s', enhancement)
            MY_LOGGER.debug('tweet_text = %s', tweet_text)

        description = ''
        for enhancement_group in IMAGE_OPTIONS['enhancements']:
            if IMAGE_OPTIONS['enhancements'][enhancement_group]['filename'] == enhancement:
                description = IMAGE_OPTIONS['enhancements'][enhancement_group]['description']
        MY_LOGGER.debug('>> %s', description)
 
 

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
