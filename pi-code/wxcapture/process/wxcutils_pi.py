#!/usr/bin/env python3
"""wxcapture utility code Pi specific functionality"""


# import libraries
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from rtlsdr import RtlSdr
import tweepy
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
    tt_auth = tweepy.OAuthHandler(TT_CONFIG['consumer key'], TT_CONFIG['consumer secret'])
    tt_auth.set_access_token(TT_CONFIG['access token'], TT_CONFIG['access token secret'])

    # get api
    tt_api = tweepy.API(tt_auth)

    # send tweet
    tt_status = tt_api.update_with_media(tt_image_file, tt_text)


FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_UTIL_LOGGER = get_logger('wxcutils_pi', '/home/pi/wxcapture/process/logs/', 'wxcutils_pi.log')
