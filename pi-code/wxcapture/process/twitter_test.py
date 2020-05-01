#!/usr/bin/env python3
"""twitter tweet test"""


# import libraries
import os

from datetime import datetime
from datetime import datetime, date, time, timedelta
import tweepy
from tweepy import Cursor
import wxcutils
import wxcutils_pi


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
MODULE = 'twitter_test'
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

CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-twitter.json')

# authentication
MY_LOGGER.debug('Authenticating to Twitter API')
AUTH = tweepy.OAuthHandler(CONFIG['consumer key'], CONFIG['consumer secret'])
AUTH.set_access_token(CONFIG['access token'], CONFIG['access token secret'])

# get api
auth_api = tweepy.API(AUTH)

twitter_handle = 'RaspberryPiNZ'

MY_LOGGER.debug("Getting data for %s", twitter_handle)
item = auth_api.get_user(twitter_handle)
MY_LOGGER.debug("name: %s", item.name)
MY_LOGGER.debug("screen_name: %s", item.screen_name)
MY_LOGGER.debug("description: %s", item.description)
MY_LOGGER.debug("statuses_count: %s", str(item.statuses_count))
MY_LOGGER.debug("friends_count: %s", str(item.friends_count))
MY_LOGGER.debug("followers_count: %s", str(item.followers_count))

MY_LOGGER.debug('looking at posts')
hashtags = []
mentions = []
tweet_count = 0
end_date = datetime.utcnow() - timedelta(days=1)
for status in Cursor(auth_api.user_timeline, id=twitter_handle).items():
    tweet_count += 1
    MY_LOGGER.debug('counter = %d', tweet_count)
    MY_LOGGER.debug(status)

    break


# wxcutils_pi.tweet_text(CONFIG_PATH, 'config-twitter.json',
#                       'hello world (original I know) ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# wxcutils_pi.tweet_text_image(CONFIG_PATH, 'config-twitter.json',
#                              'hello world with image (original I know) ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
#                              IMAGE_PATH + '2020-04-18-20-11-28-NOAA_18-norm-tn.jpg')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
