#!/usr/bin/env python3
"""tweet images"""


# import libraries
import os
from os import path
import time
import sys
import tweepy
import wxcutils


def tweet_text_image(tt_config_path, tt_config_file, tt_text, tt_image_file):
    """tweet text with image using info from the config file"""
    tt_config = wxcutils.load_json(tt_config_path, tt_config_file)

    # authentication
    MY_LOGGER.debug('Authenticating to Twitter API')
    tt_auth = tweepy.OAuthHandler(tt_config['consumer key'], tt_config['consumer secret'])
    tt_auth.set_access_token(tt_config['access token'], tt_config['access token secret'])

    # get api
    tt_api = tweepy.API(tt_auth)

    # send tweet
    MY_LOGGER.debug('Sending tweet with text = %s, image = %s', tt_text, tt_image_file)
    tt_status = tt_api.update_with_media(tt_image_file, tt_text)
    MY_LOGGER.debug('Tweet sent with status = %s', tt_status)


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
MODULE = 'tweet'
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
    # tweet image
    MY_LOGGER.debug('Tweeting image')
    TWEET_TEXT = 'Latest weather satellite image from GK-2A #weather #satellite. ' + \
        'See more at https://kiwiweather.com. Click on image to see more detail.'
    # files are ~ 2MB, so can tweet full size image
    TWEET_IMAGE = OUTPUT_PATH + 'sanchez.jpg'
    # only proceed if the image exists and less than an hour old
    IMAGE_AGE = time.time() - os.stat(TWEET_IMAGE).st_mtime
    MY_LOGGER.debug('IMAGE_AGE = %f', IMAGE_AGE)
    if path.exists(TWEET_IMAGE) and IMAGE_AGE < 3600:
        try:
            tweet_text_image(CONFIG_PATH, 'config-twitter.json',
                             TWEET_TEXT, TWEET_IMAGE)
        except:
            MY_LOGGER.critical('Tweet exception handler: %s %s %s',
                               sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        MY_LOGGER.debug('Tweeted!')
    else:
        MY_LOGGER.debug('The image, %s, does not exist so skipping tweeting it.',
                        TWEET_IMAGE)

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
