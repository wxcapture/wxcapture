#!/usr/bin/env python3
"""tweet Sanchez images"""


# import libraries
import os
from os import path
import sys
import time
import requests
import tweepy
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

    MY_LOGGER.debug('Dark')
    return False


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


def tweet(image, text):
    """do the tweets"""

    try:
        # tweet image
        MY_LOGGER.debug('Tweeting %s for image %s', text, image)
        # only proceed if the image exists
        if path.exists(OUTPUT_PATH + image):
            try:
                tweet_text_image(CONFIG_PATH, 'config-twitter.json',
                                 text, OUTPUT_PATH + image)
            except:
                MY_LOGGER.critical('Tweet exception handler: %s %s %s',
                                   sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            MY_LOGGER.debug('Tweeted!')
        else:
            MY_LOGGER.debug('The image, %s, does not exist so skipping tweeting it.',
                            image)

    except:
        MY_LOGGER.critical('Global exception handler: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


def get_image_age(image):
    """find the age of the image in seconds"""
    image_age = time.time() - os.stat(OUTPUT_PATH + image).st_mtime
    MY_LOGGER.debug('image_age = %f', image_age)
    return image_age


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

URL_BASE = 'https://kiwiweather.com/goes/'
MY_LOGGER.debug('URL_BASE = %s', URL_BASE)
THRESHOLD = 25
MY_LOGGER.debug('THRESHOLD = %d', THRESHOLD)

# do each tweet, if image is less than an hour old
# GOES 17
IMAGE = 'goes_17_fd_fc-tn.jpg'
if get_image_age(IMAGE) < 3600:
    tweet(IMAGE,
          'Latest GOES 17 weather satellite full colour image. ' +
          'See more at https://kiwiweather.com. #weather #satellite #GOES17')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

IMAGE = 'goes_17_m1_fc-tn.jpg'
if get_image_age(IMAGE) < 3600:
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, tweeting', IMAGE)
        tweet(IMAGE,
              'Latest GOES 17 weather satellite full colour detail image (normally California). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES17')
    else:
        MY_LOGGER.debug('%s is dark, not tweeting visible, so using IR shortwave', IMAGE)
        tweet('goes_17_m1_ch07-tn.jpg',
              'Latest GOES 17 weather satellite infra red image (normally California). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES17')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

IMAGE = 'goes_17_m2_fc-tn.jpg'
if get_image_age(IMAGE) < 3600:
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, tweeting', IMAGE)
        tweet(IMAGE,
              'Latest GOES 17 weather satellite full colour detail image (normally Alaska). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES17')
    else:
        MY_LOGGER.debug('%s is dark, not tweeting visible, so using IR shortwave', IMAGE)
        tweet('goes_17_m2_ch07-tn.jpg',
              'Latest GOES 17 weather satellite infra red image (normally Alaska). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES17')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

# GOES 16
IMAGE = 'goes_16_fd_ch13_enhanced-tn.jpg'
if get_image_age(IMAGE) < 3600:
    tweet(IMAGE,
          'Latest GOES 16 weather satellite enhanced IR image. ' +
          'See more at https://kiwiweather.com. #weather #satellite #GOES16')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

# GOES 15
IMAGE = 'goes_15_fd_IR-tn.jpg'
if get_image_age(IMAGE) < 3600:
    tweet(IMAGE,
          'Latest GOES 15 weather satellite enhanced IR image. ' +
          'See more at https://kiwiweather.com. #weather #satellite #GOES15')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

IMAGE = 'goes_15_combine-north_IR-tn.jpg'
if get_image_age(IMAGE) < 3600:
    tweet(IMAGE,
          'Latest GOES 15 weather satellite enhanced IR/WV image - USA, Canada, Pacific. ' +
          'See more at https://kiwiweather.com. #weather #satellite #GOES15')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

# GOES 15 GVR
IMAGE = 'goes15gvar-FC-tn.jpg'
if get_image_age(IMAGE) < 3600:
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, tweeting', IMAGE)
        tweet(IMAGE,
              'Latest GOES 15 weather satellite full colour image (US, Canada, Pacific). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES15')
    else:
        MY_LOGGER.debug('%s is dark, not tweeting visible, so using IR', IMAGE)
        tweet('goes15gvar-4-tn.jpg',
              'Latest GOES 15 weather satellite infra red image (US, Canada, Pacific). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES15')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

# GOES 14
IMAGE = 'goes14-FC-tn.jpg'
if get_image_age(IMAGE) < 3600:
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, tweeting', IMAGE)
        tweet(IMAGE,
              'Latest GOES 14 weather satellite full colour image (US, Canada, Pacific). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES14')
    else:
        MY_LOGGER.debug('%s is dark, not tweeting visible, so using IR', IMAGE)
        tweet('goes14-4-tn.jpg',
              'Latest GOES 14 weather satellite infra red image (US, Canada, Pacific). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES14')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

# GOES 13
IMAGE = 'goes13-FC-tn.jpg'
if get_image_age(IMAGE) < 3600:
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, tweeting', IMAGE)
        tweet(IMAGE,
              'Latest GOES 13 weather satellite full colour image (US, Canada, Pacific). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES13')
    else:
        MY_LOGGER.debug('%s is dark, not tweeting visible, so using IR', IMAGE)
        tweet('goes13-4-tn.jpg',
              'Latest GOES 13 weather satellite infra red image (US, Canada, Pacific). ' +
              'See more at https://kiwiweather.com. #weather #satellite #GOES13')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)


# Himawari 8
IMAGE = 'himawari_8_fd_IR-tn.jpg'
if get_image_age(IMAGE) < 3600:
    tweet(IMAGE,
          'Latest Himawari 8 weather satellite enhanced IR image. ' +
          'See more at https://kiwiweather.com. #weather #satellite #Himawari8')
else:
    MY_LOGGER.debug('Image %s is too old', IMAGE)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
