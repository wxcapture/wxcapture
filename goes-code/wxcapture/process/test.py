#!/usr/bin/env python3
"""test code """


# import libraries
import os
import sys
import requests
import cv2
import numpy as np
import wxcutils

def find_circle(filename, extension):
    """find the circle in the image"""
    MY_LOGGER.debug('=' * 40)
    MY_LOGGER.debug('Processing file %s%s', filename, extension)

    x_step = 1
    x_step_neg = -1 * x_step
    threshold = 75

    MY_LOGGER.debug('Loading file')
    image = cv2.imread(CODE_PATH + filename + extension)
    MY_LOGGER.debug('Convert to grayscale')

    x_res = image.shape[1]
    y_res = image.shape[0]
    MY_LOGGER.debug('Resolution x = %d, y = %d', x_res, y_res)
    x_max = x_res - 1
    x_limit = int(x_max / 8)
    y_mid = int(y_res / 2)

    x_left = 0
    MY_LOGGER.debug('Left edge')
    for x_counter in range(0, x_limit, x_step):
        pixel = image[y_mid, x_counter][0] + image[y_mid, x_counter][1] + image[y_mid, x_counter][2]
        cv2.line(image, (x_counter, 0), (x_counter, y_mid -1), (0, 255, 0), 10)
        if pixel <= threshold:
            x_left = x_counter
        else:
            break

    x_right = x_res - 1
    MY_LOGGER.debug('Right edge')
    for x_counter in range(x_max, x_max - x_limit ,x_step_neg):
        pixel = image[y_mid, x_counter][0] + image[y_mid, x_counter][1] + image[y_mid, x_counter][2]
        cv2.line(image, (x_counter, 0), (x_counter, y_mid -1), (0, 255, 0), 10)
        if pixel <= threshold:
            x_right = x_counter
        else:
            break


    MY_LOGGER.debug('x_left = %d, x_right = %d', x_left, x_right)
    radius = int((x_right - x_left) * 0.5)
    x_centre = x_left + radius
    MY_LOGGER.debug('x_centre = %s, radius = %d', x_centre, radius)

    # draw circle
    MY_LOGGER.debug('Drawing circle')
    cv2.circle(image, (x_centre, y_mid), radius, (0, 255, 0), 2)

    MY_LOGGER.debug('Writing out the image')
    cv2.imwrite(CODE_PATH + filename + '-processed' + extension, image)
    MY_LOGGER.debug('=' * 40)


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

MY_LOGGER.debug('Left example - bad circle')
find_circle('five-left', '.jpg')
MY_LOGGER.debug('Left example - bad circle')
find_circle('four-left', '.jpg')
MY_LOGGER.debug('Right example - good circle')
find_circle('three-right', '.jpg')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
