#!/usr/bin/env python3
"""process Meteor files to remove noise"""

# import libraries
import os
import sys
from PIL import Image
import wxcutils

def load_image(li_filename):
    """load an image file"""
    global IMAGE
    global IMAGE_HEIGHT
    global IMAGE_WIDTH
    IMAGE = Image.open(li_filename)
    IMAGE_HEIGHT = IMAGE.size[1]
    IMAGE_WIDTH = IMAGE.size[0]
    MY_LOGGER.debug('Loaded image %s height = %d width = %d type = %s',
                    li_filename, IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE.format)


def save_image(si_filename):
    """save an image file"""
    MY_LOGGER.debug('Saving %s', si_filename)
    IMAGE.save(si_filename)
    MY_LOGGER.debug('Saved %s', si_filename)


def fix_thick_line(ftl_start, ftl_end):
    """fix thick black lines"""
    MY_LOGGER.debug('Thick black line to fix between lines %d and %d of thickness %d', ftl_start, ftl_end, ftl_end - ftl_start)
    MY_LOGGER.debug('Needs some code adding once I figure how best to handle this!')
        

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
MODULE = 'metline'
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

IMAGE_HEIGHT = 0
IMAGE_WIDTH = 0
IMAGE = Image.new('RGB', (1, 1), (0, 0, 0))
MIN_PIXEL_THICK_LENGTH = 30
FIXED_CYAN = 0
FIXED_MAGENTA = 0
FIXED_YELLOW = 0
FIXED_BLACK = 0
FIXED_RED = 0
FIXED_GREEN = 0
FIXED_BLUE = 0

try:
    MY_LOGGER.debug('Load image start')
    load_image(WORKING_PATH + 'meteor.bmp')
    MY_LOGGER.debug('Load image end')

    MY_LOGGER.debug('Find thick lines start')
    IMAGE_MID_WIDTH = int(IMAGE_WIDTH / 2)
    Y_ITERATOR = 0
    BLACK_RUN_LENGTH = 0
    BLACK_RUN_START = 0
    while Y_ITERATOR < IMAGE_HEIGHT:
        # MY_LOGGER.debug('Y_ITERATOR = %d', Y_ITERATOR)
        RED, GREEN, BLUE = IMAGE.getpixel((IMAGE_MID_WIDTH, Y_ITERATOR))
        if RED == 0 and GREEN == 0 and BLUE == 0:
            BLACK_RUN_START = Y_ITERATOR
            BLACK_RUN_LENGTH += 1
            # MY_LOGGER.debug('BLACK Y_ITERATOR = %d, run = %d', Y_ITERATOR, BLACK_RUN_LENGTH)
        else:
            if BLACK_RUN_LENGTH > 1 and BLACK_RUN_LENGTH >= MIN_PIXEL_THICK_LENGTH:
                # MY_LOGGER.debug('Thick black run total length = %d between lines %d and %d', BLACK_RUN_LENGTH, BLACK_RUN_START, BLACK_RUN_START + BLACK_RUN_LENGTH)
                fix_thick_line(BLACK_RUN_START - BLACK_RUN_LENGTH, BLACK_RUN_START)
            BLACK_RUN_LENGTH = 0

        Y_ITERATOR += 1
    MY_LOGGER.debug('Find thick lines end')


    MY_LOGGER.debug('Image line removal start')
    Y_ITERATOR = 1
    while Y_ITERATOR < IMAGE_HEIGHT:
        X_ITERATOR = 0
        while X_ITERATOR < IMAGE_WIDTH:
            RED, GREEN, BLUE = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR))
            # MY_LOGGER.debug('Pixel %d,%d = R%d G%d B%d', X_ITERATOR, Y_ITERATOR, RED, green, blue)
            # see if cyan is faulty
            if RED == 0 and GREEN != 0 and BLUE != 0:
                # MY_LOGGER.debug('bad cyan')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing cyan')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN, BLUE))
                FIXED_CYAN += 1
            # see if magenta is faulty
            if RED != 0 and GREEN == 0 and BLUE != 0:
                # MY_LOGGER.debug('bad magenta')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing magenta')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED, GREEN_BELOW, BLUE))
                FIXED_MAGENTA += 1
            # see if yellow is faulty
            if RED != 0 and GREEN != 0 and BLUE == 0:
                 # MY_LOGGER.debug('bad yellow')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing yellow')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED, GREEN, BLUE_BELOW))
                FIXED_YELLOW += 1
            # see if black is faulty
            if RED == 0 and GREEN == 0 and BLUE == 0:
                 # MY_LOGGER.debug('bad black')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing black')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN_BELOW, BLUE_BELOW))
                FIXED_BLACK += 1
            if RED != 0 and GREEN == 0 and BLUE == 0:
                # MY_LOGGER.debug('bad red')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing red')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED, GREEN_BELOW, BLUE_BELOW))
                FIXED_RED += 1
            if RED == 0 and GREEN != 0 and BLUE == 0:
                # MY_LOGGER.debug('bad green')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing green')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN, BLUE_BELOW))
                FIXED_GREEN += 1
            if RED == 0 and GREEN == 0 and BLUE != 0:
                # MY_LOGGER.debug('bad blue')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_LOGGER.debug('fixing blue')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN_BELOW, BLUE))
                FIXED_GREEN += 1

            X_ITERATOR += 1
        Y_ITERATOR += 1

    MY_LOGGER.debug('Fixed cyan = %d', FIXED_CYAN)
    MY_LOGGER.debug('Fixed magenta = %d', FIXED_MAGENTA)
    MY_LOGGER.debug('Fixed yellow = %d', FIXED_YELLOW)
    MY_LOGGER.debug('Fixed black = %d', FIXED_BLACK)
    MY_LOGGER.debug('Fixed red = %d', FIXED_RED)
    MY_LOGGER.debug('Fixed green = %d', FIXED_GREEN)
    MY_LOGGER.debug('Fixed blue = %d', FIXED_BLUE)
    MY_LOGGER.debug('Image line removal finished')

    MY_LOGGER.debug('Save image start')
    save_image(WORKING_PATH + 'meteorFIX.bmp')
    MY_LOGGER.debug('Save image end')

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
