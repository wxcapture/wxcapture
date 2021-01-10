#!/usr/bin/env python3
"""test code to find main colour in image"""


# import libraries
import os
import sys
import requests
import cv2
import wxcutils


def is_light(filename, threshold):
    """see if the image is not dark"""
    try:
        MY_LOGGER.debug('Reading file from URL')
        data = requests.get(URL_BASE + filename)
        MY_LOGGER.debug('Writing file')
        open(WORKING_PATH + filename, 'wb').write(data.content)

        MY_LOGGER.debug('Reading file')
        img = cv2.imread(WORKING_PATH + filename)
        mean_components = img.mean(axis=0).mean(axis=0)
        mean = (mean_components[0] + mean_components[1] + mean_components[2]) / 3

        if mean > threshold:
            MY_LOGGER.debug('Light - %f', mean)
            return True
    except:
        MY_LOGGER.critical('is_light exception handler: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

    MY_LOGGER.debug('Dark - %f', mean)
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


URL_BASE = 'https://kiwiweather.com/goes/'

if is_light('goes_17_m1_fc-tn.jpg', 5):
    MY_LOGGER.debug('is Light')
else:
    MY_LOGGER.debug('is Dark')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
