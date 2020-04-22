#!/usr/bin/env python3
"""wxcapture utility code Pi specific functionality"""


# import libraries
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from rtlsdr import RtlSdr
import tweepy
from PIL import Image, ImageOps
import wxcutils


def get_console_handler():
    """Get logger console handler"""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(path, log_file):
    """Get logger file handler"""
    file_handler = TimedRotatingFileHandler(path + log_file, when='midnight', backupCount=7)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name, path, log_file):
    """Create logger"""
    global MY_UTIL_LOGGER
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(path, log_file))
    logger.propagate = False
    MY_UTIL_LOGGER = logger
    return logger


def get_sdr_device(sdr_serial_number):
    """ get SDR device ID from the serial number"""
    return RtlSdr.get_device_index_by_serial(sdr_serial_number)


def tweet_text(tt_config_path, tt_config_file, tt_text):
    """tweet text using info from the config file"""
    tt_config = wxcutils.load_json(tt_config_path, tt_config_file)

    # authentication
    tt_auth = tweepy.OAuthHandler(tt_config['consumer key'], tt_config['consumer secret'])
    tt_auth.set_access_token(tt_config['access token'], tt_config['access token secret'])

    # get api
    tt_api = tweepy.API(tt_auth)

    # send tweet
    tt_api.update_status(tt_text)


def tweet_text_image(tt_config_path, tt_config_file, tt_text, tt_image_file):
    """tweet text with image using info from the config file"""
    TT_CONFIG = wxcutils.load_json(tt_config_path, tt_config_file)

    # authentication
    MY_UTIL_LOGGER.debug('Authenitcating to Twitter API')
    tt_auth = tweepy.OAuthHandler(TT_CONFIG['consumer key'], TT_CONFIG['consumer secret'])
    tt_auth.set_access_token(TT_CONFIG['access token'], TT_CONFIG['access token secret'])

    # get api
    tt_api = tweepy.API(tt_auth)

    # send tweet
    MY_UTIL_LOGGER.debug('Sending tweet with text = %s, image = %s', tt_text, tt_image_file)
    tt_status = tt_api.update_with_media(tt_image_file, tt_text)
    MY_UTIL_LOGGER.debug('Tweet sent with status = %s', tt_status)


def fix_image(fi_source, fi_destination, fi_equalize):
    """remove noise from image"""

    def load_image(li_filename):
        """load an image file"""
        li_image = Image.open(li_filename)
        li_image_height = li_image.size[1]
        li_image_width = li_image.size[0]
        MY_UTIL_LOGGER.debug('Loaded image %s height = %d width = %d type = %s',
                             li_filename, li_image_height, li_image_width, li_image.format)
        return li_image, li_image_height, li_image_width


    def save_image(si_filename):
        """save an image file"""
        MY_UTIL_LOGGER.debug('Saving %s', si_filename)
        IMAGE.save(si_filename)
        MY_UTIL_LOGGER.debug('Saved %s', si_filename)


    def fix_thick_line(ftl_start, ftl_end):
        """fix thick black lines"""
        MY_UTIL_LOGGER.debug('Thick black line to fix between lines %d and %d of thickness %d', ftl_start, ftl_end, ftl_end - ftl_start)
        MY_UTIL_LOGGER.debug('Needs some code adding once I figure how best to handle this!')



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

    MY_UTIL_LOGGER.debug('Load image start')
    IMAGE, IMAGE_HEIGHT, IMAGE_WIDTH = load_image(fi_source)
    MY_UTIL_LOGGER.debug('Load image end')

    MY_UTIL_LOGGER.debug('Find thick lines start')
    IMAGE_MID_WIDTH = int(IMAGE_WIDTH / 2)
    Y_ITERATOR = 0
    BLACK_RUN_LENGTH = 0
    BLACK_RUN_START = 0
    while Y_ITERATOR < IMAGE_HEIGHT:
        # MY_UTIL_LOGGER.debug('Y_ITERATOR = %d', Y_ITERATOR)
        RED, GREEN, BLUE = IMAGE.getpixel((IMAGE_MID_WIDTH, Y_ITERATOR))
        if RED == 0 and GREEN == 0 and BLUE == 0:
            BLACK_RUN_START = Y_ITERATOR
            BLACK_RUN_LENGTH += 1
            # MY_UTIL_LOGGER.debug('BLACK Y_ITERATOR = %d, run = %d', Y_ITERATOR, BLACK_RUN_LENGTH)
        else:
            if BLACK_RUN_LENGTH > 1 and BLACK_RUN_LENGTH >= MIN_PIXEL_THICK_LENGTH:
                # MY_UTIL_LOGGER.debug('Thick black run total length = %d between lines %d and %d', BLACK_RUN_LENGTH, BLACK_RUN_START, BLACK_RUN_START + BLACK_RUN_LENGTH)
                fix_thick_line(BLACK_RUN_START - BLACK_RUN_LENGTH, BLACK_RUN_START)
            BLACK_RUN_LENGTH = 0

        Y_ITERATOR += 1
    MY_UTIL_LOGGER.debug('Find thick lines end')


    MY_UTIL_LOGGER.debug('Image line removal start')
    Y_ITERATOR = 1
    while Y_ITERATOR < IMAGE_HEIGHT:
        MY_UTIL_LOGGER.debug(Y_ITERATOR)
        X_ITERATOR = 0
        while X_ITERATOR < IMAGE_WIDTH:
            RED, GREEN, BLUE = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR))
            # MY_UTIL_LOGGER.debug('Pixel %d,%d = R%d G%d B%d', X_ITERATOR, Y_ITERATOR, RED, green, blue)
            # see if cyan is faulty
            if RED == 0 and GREEN != 0 and BLUE != 0:
                # MY_UTIL_LOGGER.debug('bad cyan')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing cyan')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN, BLUE))
                FIXED_CYAN += 1
            # see if magenta is faulty
            if RED != 0 and GREEN == 0 and BLUE != 0:
                # MY_UTIL_LOGGER.debug('bad magenta')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing magenta')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED, GREEN_BELOW, BLUE))
                FIXED_MAGENTA += 1
            # see if yellow is faulty
            if RED != 0 and GREEN != 0 and BLUE == 0:
                # MY_UTIL_LOGGER.debug('bad yellow')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing yellow')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED, GREEN, BLUE_BELOW))
                FIXED_YELLOW += 1
            # see if black is faulty
            if RED == 0 and GREEN == 0 and BLUE == 0:
                # MY_UTIL_LOGGER.debug('bad black')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing black')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN_BELOW, BLUE_BELOW))
                FIXED_BLACK += 1
            if RED != 0 and GREEN == 0 and BLUE == 0:
                # MY_UTIL_LOGGER.debug('bad red')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing red')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED, GREEN_BELOW, BLUE_BELOW))
                FIXED_RED += 1
            if RED == 0 and GREEN != 0 and BLUE == 0:
                # MY_UTIL_LOGGER.debug('bad green')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing green')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN, BLUE_BELOW))
                FIXED_GREEN += 1
            if RED == 0 and GREEN == 0 and BLUE != 0:
                # MY_UTIL_LOGGER.debug('bad blue')
                RED_BELOW, GREEN_BELOW, BLUE_BELOW = IMAGE.getpixel((X_ITERATOR, Y_ITERATOR - 1))
                # MY_UTIL_LOGGER.debug('fixing blue')
                IMAGE.putpixel((X_ITERATOR, Y_ITERATOR), (RED_BELOW, GREEN_BELOW, BLUE))
                FIXED_BLUE += 1

            X_ITERATOR += 1
        Y_ITERATOR += 1

    MY_UTIL_LOGGER.debug('Fixed cyan = %d', FIXED_CYAN)
    MY_UTIL_LOGGER.debug('Fixed magenta = %d', FIXED_MAGENTA)
    MY_UTIL_LOGGER.debug('Fixed yellow = %d', FIXED_YELLOW)
    MY_UTIL_LOGGER.debug('Fixed black = %d', FIXED_BLACK)
    MY_UTIL_LOGGER.debug('Fixed red = %d', FIXED_RED)
    MY_UTIL_LOGGER.debug('Fixed green = %d', FIXED_GREEN)
    MY_UTIL_LOGGER.debug('Fixed blue = %d', FIXED_BLUE)
    MY_UTIL_LOGGER.debug('Image line removal finished')

    if fi_equalize == 'Y':
        MY_UTIL_LOGGER.debug('Equalising image start')
        IMAGE = ImageOps.equalize(IMAGE, mask = None)
        MY_UTIL_LOGGER.debug('Equalising image end')

    MY_UTIL_LOGGER.debug('Save image start')
    save_image(fi_destination)
    MY_UTIL_LOGGER.debug('Save image end')





FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_UTIL_LOGGER = get_logger('wxcutils_pi', '/home/pi/wxcapture/process/logs/', 'wxcutils_pi.log')
