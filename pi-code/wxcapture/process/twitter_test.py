#!/usr/bin/env python3
"""twitter tweet test"""


# import libraries
import os

from datetime import datetime
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



# wxcutils_pi.tweet_text(CONFIG_PATH, 'config-twitter.json',
#                       'hello world (original I know) ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# wxcutils_pi.tweet_text_image(CONFIG_PATH, 'config-twitter.json',
#                              'hello world with image (original I know) ' + datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
#                              IMAGE_PATH + '2020-04-18-20-11-28-NOAA_18-norm-tn.jpg')

wxcutils_pi.webhooks(CONFIG_PATH, 'config-discord.json',
                     'http://pbs.twimg.com/media/EW9jYMeU0AAIobA.jpg',
                     'NOAA 19', 'Manual Test - Pass over Auckland, New Zealand', 'ff0000',
                     '63', '912', '04:33:35 April 30  2020 (NZST)',
                     '1 (visible)', '4 (thermal infred)')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')