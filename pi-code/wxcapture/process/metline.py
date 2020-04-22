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
MIN_PIXEL_LINE_LENGTH = 50
FIXED_CYAN = 0
FIXED_MAGENTA = 0
FIXED_YELLOW = 0
FIXED_BLACK = 0
FIXED_RED = 0
FIXED_GREEN = 0
FIXED_BLUE = 0

try:
    
    load_image(WORKING_PATH + 'meteor.bmp')

    MY_LOGGER.debug('Image line removal start')
    y_iterator = 1
    while y_iterator < IMAGE_HEIGHT:
        x_iterator = 0
        while x_iterator < IMAGE_WIDTH:
            red, green, blue = IMAGE.getpixel((x_iterator, y_iterator))
            # MY_LOGGER.debug('Pixel %d,%d = R%d G%d B%d', x_iterator, y_iterator, red, green, blue)
            # see if cyan is faulty
            if red == 0 and green != 0 and blue != 0:
                # MY_LOGGER.debug('bad cyan')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing cyan')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red_below, green, blue))
                FIXED_CYAN += 1
            # see if magenta is faulty
            if red != 0 and green == 0 and blue != 0:
                # MY_LOGGER.debug('bad magenta')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing magenta')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red, green_below, blue))
                FIXED_MAGENTA +- 1
            # see if yellow is faulty
            if red != 0 and green != 0 and blue == 0:
                 # MY_LOGGER.debug('bad yellow')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing yellow')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red, green, blue_below))
                FIXED_YELLOW += 1
            # see if black is faulty
            if red == 0 and green == 0 and blue == 0:
                 # MY_LOGGER.debug('bad black')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing black')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red_below, green_below, blue_below))
                FIXED_BLACK += 1
            if red != 0 and green == 0 and blue == 0:
                # MY_LOGGER.debug('bad red')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing red')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red, green_below, blue_below))
                FIXED_RED += 1
            if red == 0 and green != 0 and blue == 0:
                # MY_LOGGER.debug('bad green')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing green')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red_below, green, blue_below))
                FIXED_GREEN += 1
            if red == 0 and green == 0 and blue != 0:
                # MY_LOGGER.debug('bad blue')
                red_below, green_below, blue_below = IMAGE.getpixel((x_iterator, y_iterator - 1))
                # MY_LOGGER.debug('fixing blue')
                IMAGE.putpixel((x_iterator, y_iterator) ,(red_below, green_below, blue))
                FIXED_GREEN += 1

            x_iterator += 1
        y_iterator += 1

    MY_LOGGER.debug('Fixed cyan = %d', FIXED_CYAN)
    MY_LOGGER.debug('Fixed magenta = %d', FIXED_MAGENTA)
    MY_LOGGER.debug('Fixed yellow = %d', FIXED_YELLOW)
    MY_LOGGER.debug('Fixed black = %d', FIXED_BLACK)
    MY_LOGGER.debug('Fixed red = %d', FIXED_RED)
    MY_LOGGER.debug('Fixed green = %d', FIXED_GREEN)
    MY_LOGGER.debug('Fixed blue = %d', FIXED_BLUE)
    MY_LOGGER.debug('Image line removal finished')

    # IMAGE.show()
    save_image(WORKING_PATH + 'meteorFIX.bmp')

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
