#!/usr/bin/env python3
"""test code """


# import libraries
import os
import sys
import math
import numpy as np
import cv2
import wxcutils


def centre_image(filename, extension):
    """find the circle in the image"""
    def get_pixel_intensity(pi_x, pi_y):
        """get the pixel intensity"""
        # note range will be 0 - (255*3)
        return image[pi_y, pi_x][0] + image[pi_y, pi_x][1] + image[pi_y, pi_x][2]

    MY_LOGGER.debug('=' * 40)
    MY_LOGGER.debug('Processing file %s%s', filename, extension)

    image = cv2.imread(filename + extension)

    x_res = image.shape[1]
    y_res = image.shape[0]
    MY_LOGGER.debug('x_res = %d, y_res = %d', x_res, y_res)

    x_border = int(x_res * (456 / 5206))
    MY_LOGGER.debug('x_border = %d', x_border)

    # detect border via sampling
    MY_LOGGER.debug('Sampling test - left')
    left_int = 0
    for x in range(0, x_border, 20):
        for y in range(0, y_res - 1, 20):
            left_int += get_pixel_intensity(x, y)
    MY_LOGGER.debug('left_int = %d', left_int)

    MY_LOGGER.debug('Sampling test - right')
    right_int = 0
    for x in range(x_res - x_border - 1, x_res - 1, 20):
        for y in range(0, y_res - 1, 20):
            right_int += get_pixel_intensity(x, y)
    MY_LOGGER.debug('right_int = %d', right_int)

    if left_int > right_int:
        MY_LOGGER.debug('Left aligned')
        new_image = image[0:y_res-1, 0:x_res-x_border]
    else:
        MY_LOGGER.debug('Right aligned')
        new_image = image[0:y_res-1, x_border:x_res-1]

    MY_LOGGER.debug('write out image')
    cv2.imwrite(filename + '-centred' +  extension, new_image)   

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


centre_image('5-1', '.jpg')
centre_image('5-2', '.jpg')
centre_image('5-3', '.jpg')
centre_image('5-4', '.jpg')
centre_image('5-5', '.jpg')
centre_image('FC-1', '.jpg')
centre_image('FC-2', '.jpg')
centre_image('FC-3', '.jpg')
centre_image('FC-4', '.jpg')
centre_image('FC-5', '.jpg')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
