#!/usr/bin/env python3
"""wxcapture utility code Pi specific functionality"""


# import libraries
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import time
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
    logger.propagate = True
    MY_UTIL_LOGGER = logger
    MY_UTIL_LOGGER.debug('logger created for %s %s %s', logger_name, path, log_file)
    return logger


def get_sdr_device(sdr_serial_number):
    """ get SDR device ID from the serial number"""
    return RtlSdr.get_device_index_by_serial(sdr_serial_number)


def tweet_text(tt_config_path, tt_config_file, tt_text):
    """tweet text using info from the config file"""
    tt_config = wxcutils.load_json(tt_config_path, tt_config_file)

    # authentication
    MY_UTIL_LOGGER.debug('Authenticating to Twitter API')
    tt_auth = tweepy.OAuthHandler(tt_config['consumer key'], tt_config['consumer secret'])
    tt_auth.set_access_token(tt_config['access token'], tt_config['access token secret'])

    # get api
    tt_api = tweepy.API(tt_auth)

    # send tweet
    MY_UTIL_LOGGER.debug('Sending tweet with text = %s', tt_text)
    tt_api.update_status(tt_text)
    MY_UTIL_LOGGER.debug('Tweet sent')


def tweet_text_image(tt_config_path, tt_config_file, tt_text, tt_image_file):
    """tweet text with image using info from the config file"""
    tt_config = wxcutils.load_json(tt_config_path, tt_config_file)

    # authentication
    MY_UTIL_LOGGER.debug('Authenticating to Twitter API')
    tt_auth = tweepy.OAuthHandler(tt_config['consumer key'], tt_config['consumer secret'])
    tt_auth.set_access_token(tt_config['access token'], tt_config['access token secret'])

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
        image.save(si_filename)
        MY_UTIL_LOGGER.debug('Saved %s', si_filename)


    def fix_thick_line(ftl_start, ftl_end):
        """fix thick black lines"""
        MY_UTIL_LOGGER.debug('Thick black line to fix between lines %d and %d of thickness %d', ftl_start, ftl_end, ftl_end - ftl_start)
        MY_UTIL_LOGGER.debug('Needs some code adding once I figure how best to handle this!')


    image_height = 0
    image_width = 0
    image = Image.new('RGB', (1, 1), (0, 0, 0))
    min_pixel_thick_length = 30
    fixed_cyan = 0
    fixed_magenta = 0
    fixed_yellow = 0
    fixed_black = 0
    fixed_red = 0
    fixed_green = 0
    fixed_blue = 0

    MY_UTIL_LOGGER.debug('Load image start')
    image, image_height, image_width = load_image(fi_source)
    MY_UTIL_LOGGER.debug('Load image end')

    MY_UTIL_LOGGER.debug('Find thick lines start')
    image_mid_width = int(image_width / 2)
    y_iterator = 0
    black_run_length = 0
    black_run_start = 0
    while y_iterator < image_height:
        # MY_UTIL_LOGGER.debug('y_iterator = %d', y_iterator)
        red, green, blue = image.getpixel((image_mid_width, y_iterator))
        if red == 0 and green == 0 and blue == 0:
            black_run_start = y_iterator
            black_run_length += 1
            # MY_UTIL_LOGGER.debug('BLACK y_iterator = %d, run = %d', y_iterator, black_run_length)
        else:
            if black_run_length > 1 and black_run_length >= min_pixel_thick_length:
                # MY_UTIL_LOGGER.debug('Thick black run total length = %d between lines %d and %d', black_run_length, black_run_start, black_run_start + black_run_length)
                fix_thick_line(black_run_start - black_run_length, black_run_start)
            black_run_length = 0

        y_iterator += 1
    MY_UTIL_LOGGER.debug('Find thick lines end')


    MY_UTIL_LOGGER.debug('Image line removal start')
    y_iterator = 1
    while y_iterator < image_height:
        # MY_UTIL_LOGGER.debug(y_iterator)
        x_iterator = 0
        while x_iterator < image_width:
            red, green, blue = image.getpixel((x_iterator, y_iterator))
            # MY_UTIL_LOGGER.debug('Pixel %d,%d = R%d G%d B%d', x_iterator, y_iterator, red, green, blue)
            # see if cyan is faulty
            if red == 0 and green != 0 and blue != 0:
                # MY_UTIL_LOGGER.debug('bad cyan')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing cyan')
                image.putpixel((x_iterator, y_iterator), (red_below, green, blue))
                fixed_cyan += 1
            # see if magenta is faulty
            if red != 0 and green == 0 and blue != 0:
                # MY_UTIL_LOGGER.debug('bad magenta')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing magenta')
                image.putpixel((x_iterator, y_iterator), (red, green_below, blue))
                fixed_magenta += 1
            # see if yellow is faulty
            if red != 0 and green != 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad yellow')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing yellow')
                image.putpixel((x_iterator, y_iterator), (red, green, blue_below))
                fixed_yellow += 1
            # see if black is faulty
            if red == 0 and green == 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad black')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing black')
                image.putpixel((x_iterator, y_iterator), (red_below, green_below, blue_below))
                fixed_black += 1
            if red != 0 and green == 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad red')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing red')
                image.putpixel((x_iterator, y_iterator), (red, green_below, blue_below))
                fixed_red += 1
            if red == 0 and green != 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad green')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing green')
                image.putpixel((x_iterator, y_iterator), (red_below, green, blue_below))
                fixed_green += 1
            if red == 0 and green == 0 and blue != 0:
                # MY_UTIL_LOGGER.debug('bad blue')
                red_below, green_below, blue_below = image.getpixel((x_iterator, y_iterator - 1))
                # MY_UTIL_LOGGER.debug('fixing blue')
                image.putpixel((x_iterator, y_iterator), (red_below, green_below, blue))
                fixed_blue += 1

            x_iterator += 1
        y_iterator += 1

    MY_UTIL_LOGGER.debug('Fixed cyan = %d', fixed_cyan)
    MY_UTIL_LOGGER.debug('Fixed magenta = %d', fixed_magenta)
    MY_UTIL_LOGGER.debug('Fixed yellow = %d', fixed_yellow)
    MY_UTIL_LOGGER.debug('Fixed black = %d', fixed_black)
    MY_UTIL_LOGGER.debug('Fixed red = %d', fixed_red)
    MY_UTIL_LOGGER.debug('Fixed green = %d', fixed_green)
    MY_UTIL_LOGGER.debug('Fixed blue = %d', fixed_blue)
    MY_UTIL_LOGGER.debug('Image line removal finished')

    if fi_equalize == 'Y':
        MY_UTIL_LOGGER.debug('Equalising image start')
        image = ImageOps.equalize(image, mask=None)
        MY_UTIL_LOGGER.debug('Equalising image end')

    MY_UTIL_LOGGER.debug('Save image start')
    save_image(fi_destination)
    MY_UTIL_LOGGER.debug('Save image end')


def sleep_until_start(sus_time):
    """sleep until the actual start time"""
    sus_epoch_now = time.time()
    MY_UTIL_LOGGER.debug('Actual seconds since epoch now = %f', sus_epoch_now)
    MY_UTIL_LOGGER.debug('Time required to start = %f', sus_time)
    sus_delay = sus_time - sus_epoch_now
    MY_UTIL_LOGGER.debug('Delay required = %f', sus_delay)

    if sus_delay > 0:
        MY_UTIL_LOGGER.debug('Sleeping %f seconds', sus_delay)
        time.sleep(sus_delay)
    else:
        MY_UTIL_LOGGER.debug('No sleep needed as already %f seconds late', -1 * sus_delay)
    MY_UTIL_LOGGER.debug('Ready to go on time...')


FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_UTIL_LOGGER = get_logger('wxcutils_pi', '/home/pi/wxcapture/process/logs/', 'wxcutils_pi.log')
