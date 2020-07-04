#!/usr/bin/env python3
"""Open CV test code"""

import os
import sys
import cv2
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
TEST_PATH = CODE_PATH + 'test/'

HOME = os.environ['HOME']
HOME = '/home/pi/'
FILE_PATH = HOME + '/wxcapture/process/'


def clahe(in_img):
    """do clahe create processing on image"""
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(in_img)

def do_clahe_img(img):
    """do clahe merge processing on image"""
    b_chn, g_chn, r_chn = cv2.split(img)
    return cv2.merge((clahe(b_chn), clahe(g_chn), clahe(r_chn)))

# start logging
MODULE = 'equalise'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')

try:
    INPUTS = ['test_rockface.jpg', '2020-07-02-20-43-36-METEOR-M_2-cc-rectified.jpg']

    # To over-write, leave empty
    OUTPUT = "clahe_"

    for img_file in INPUTS:
        MY_LOGGER.debug('Performing CLAHE on: \"%s\"', TEST_PATH + img_file)

        out_img = do_clahe_img(cv2.imread(TEST_PATH + img_file))

        MY_LOGGER.debug('writing \"%s\"', TEST_PATH + OUTPUT + img_file)

        cv2.imwrite(TEST_PATH + OUTPUT + img_file, out_img)

    MY_LOGGER.debug('---DONE---')

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
