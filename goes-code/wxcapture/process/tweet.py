#!/usr/bin/env python3
"""tweet images"""


# import libraries
import os
from os import path
import sys
import time
import requests
from TwitterAPI import TwitterAPI
import random
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


def send_tweet(tt_config_path, tt_config_file, tt_text, tt_file):
    """tweet text with image using info from the config file"""

    # get the Twitter API config
    tt_config = wxcutils.load_json(tt_config_path, tt_config_file)

    # authentication
    MY_LOGGER.debug('Authenticating to Twitter API')
    tt_auth = tweepy.OAuthHandler(tt_config['consumer key'], tt_config['consumer secret'])
    tt_auth.set_access_token(tt_config['access token'], tt_config['access token secret'])

    # get api
    tt_api = tweepy.API(tt_auth)

    # upload the file
    MY_LOGGER.debug('Uploading file = %s', tt_file)
    if '.jpg' in tt_file or '.gif'' in tt_file or ''.png' in tt_file:
        MY_LOGGER.debug('Image file upload')
        # upload file
        tt_media = tt_api.media_upload(tt_file)

        # send tweet
        MY_LOGGER.debug('Sending tweet with text = %s, image = %s', tt_text, tt_file)
        tt_status = tt_api.update_status(status=tt_text, media_ids=[tt_media.media_id])
    else:
        if '.mp4' in tt_file:
            MY_LOGGER.debug('Video file upload')
            # upload file
            # move to using Tweepy API when available in release 4.0.0
            tt_media_id = tt_api.media_upload(tt_file, media_category='tweet_video', chunked=True)
            
            # send tweet
            MY_LOGGER.debug('Sending tweet with text = %s, image = %s', tt_text, tt_file)
            tt_status = tt_api.update_status(status=tt_text, media_ids=[tt_media_id.media_id])
        else:
            MY_LOGGER.debug('Unknown file type - can''t upload')

    MY_LOGGER.debug('Tweet sent with status = %s', tt_status)


def get_tweet_text(image):
    """pick a random image text line from what is configured"""

    def add_text(base, add):
        """add in additional text if space available"""
        if len(base) + len(add) <= 280:
            MY_LOGGER.debug('length ok, adding')
            return base + add
        MY_LOGGER.debug('length exceeded, not adding')
        return base

    main_text = 'Satellite image'
    main_hashtag = ''
    base_hashtag = ''
    see_more = ''
    additional = ''
    for key, value in TWEETTEXT.items():
        # MY_LOGGER.debug('key = %s', key)

        if key == 'images':
            for img in TWEETTEXT[key]:
                if image == img['Filename']:
                    # select a random main text
                    random_pick = random.randint(1, 1 + len(img['Textlines'])) - 2
                    if random_pick > -1:
                        main_text = img['Textlines'][random_pick] + '. '
                    else:
                        main_text = ''
                    # select a random main hashtag
                    random_pick = random.randint(1, 1 + len(img['hashtags'])) - 2
                    if random_pick > -1:
                        main_hashtag = img['hashtags'][random_pick] + ' '
                    else:
                        main_hashtag = ''

        # select a random base hashtag
        if key == 'base hashtags':
            # MY_LOGGER.debug('key = %s, value = %s', key, value)
            random_pick = random.randint(1, 1 + len(value)) - 2
            if random_pick > -1:
                base_hashtag = value[random_pick] + ' '
            else:
                base_hashtag = ''

        # select a random see more
        if key == 'see more':
            # MY_LOGGER.debug('key = %s, value = %s', key, value)
            random_pick = random.randint(1, len(value)) - 1
            MY_LOGGER.debug('pick = %d, text = %s', random_pick, value[random_pick])
            see_more = value[random_pick] + '. '
        
        # select a random additional
        if key == 'additional':
            # MY_LOGGER.debug('key = %s, value = %s', key, value)
            random_pick = random.randint(1, len(value)) - 1
            # MY_LOGGER.debug('pick = %d, text = %s', random_pick, value[random_pick])
            additional = value[random_pick] + '. '

    # debug info
    MY_LOGGER.debug('main_text = [%s]', main_text)
    MY_LOGGER.debug('main_hashtag = [%s]', main_hashtag)
    MY_LOGGER.debug('base_hashtag = [%s]', base_hashtag)
    MY_LOGGER.debug('see_more = [%s]', see_more)
    MY_LOGGER.debug('additional = [%s]', additional)

    # add the elements, if there is space left
    text = main_text
    text = add_text(text, see_more)
    text = add_text(text, main_hashtag)
    text = add_text(text, base_hashtag)

    # add additional at random - 1 in 3 chance
    if random.randint(1, 3) == 1:
        MY_LOGGER.debug('Additional included')
        text = add_text(text, additional)
    text = add_text(text, '#KiwiWeather')

    MY_LOGGER.debug('tweet text = %s, length = %d', text, len(text))

    return text


def do_tweet(image):
    """do the tweets"""

    try:
        # tweet image
        text = get_tweet_text(image)
        MY_LOGGER.debug('Tweeting %s for image %s', text, image)
        # only proceed if the image exists
        if path.exists(OUTPUT_PATH + image):
            try:
                MY_LOGGER.debug('sending...')
                send_tweet(CONFIG_PATH, 'config-twitter.json',
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
MAXAGE = 3600
MY_LOGGER.debug('MAXAGE = %d', MAXAGE)


# load tweet text strings
TWEETTEXT = wxcutils.load_json(CONFIG_PATH, 'twitter-text.json')

# load tweet config
TWEETS = wxcutils.load_json(CONFIG_PATH, 'twitter-config.json')

THRESHOLD = int(TWEETS['Light threshold'])
MY_LOGGER.debug('THRESHOLD = %d', THRESHOLD)
MAXAGE = int(TWEETS['Max age'])
MY_LOGGER.debug('MAXAGE = %d', MAXAGE)
HOURS = int(TWEETS['Run hours'])
MY_LOGGER.debug('HOURS = %d', HOURS)

# determine delay between tweets based on number to tweet
TWEET_COUNT = 0
for key, value in TWEETS.items():
    # MY_LOGGER.debug('key = %s, value = %s', key, value)
    if key == 'Tweets':
        for tweet in value:
            TWEET_COUNT+= 1
MY_LOGGER.debug('TWEET_COUNT = %d', TWEET_COUNT)
TWEET_SLEEP = ((3600 * HOURS) - 500) / TWEET_COUNT
MY_LOGGER.debug('TWEET_SLEEP = %d', TWEET_SLEEP)

# loop forever
while True:
    # pick a tweet at random
    PICK = random.randint(1, TWEET_COUNT)
    MY_LOGGER.debug('PICK = %d', PICK)

    COUNTER = 0
    # loop through tweets to tweet
    for key, value in TWEETS.items():
        MY_LOGGER.debug('key = %s, value = %s', key, value)

        if key == 'Tweets':
            for tweet in value:
                COUNTER += 1
                # MY_LOGGER.debug('COUNTER = %d', COUNTER)
                if COUNTER == PICK:
                    try:
                        MY_LOGGER.debug('--')
                        MY_LOGGER.debug('Main Filename = %s, Main check light = %s, Alternate Filename = %s',
                                        tweet['Main Filename'], tweet['Main check light'], tweet['Alternate Filename'])
                        # is the main image young enough?
                        if get_image_age(tweet['Main Filename']) < MAXAGE:
                            # do we need to check if it is light enough?
                            if tweet['Main check light'] == "No":
                                do_tweet(tweet['Main Filename'])
                            else:
                                if is_light(tweet['Main Filename'], THRESHOLD):
                                    do_tweet(tweet['Main Filename'])
                                else:
                                    # too dark so try alternate image
                                    if get_image_age(tweet['Alternate Filename']) < MAXAGE:
                                        do_tweet(tweet['Alternate Filename'])
                                    else:
                                        MY_LOGGER.debug('Alternate image is too old')
                        else:
                            MY_LOGGER.debug('Main image is too old')
                            # see if we can use alternate image if configured?
                            if tweet['Alternate Filename'] != "":
                                if get_image_age(tweet['Alternate Filename']) < MAXAGE:
                                    do_tweet(tweet['Alternate Filename'])
                                else:
                                    MY_LOGGER.debug('Alternate image is too old')
                    except:
                        MY_LOGGER.error('exception handler: %s %s %s',
                                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                    # jump out of the loop
                    break

    # sleep to spread out tweets randomly over the time period
    SLEEP_TIME = TWEET_SLEEP * (1 + (random.random() - 0.5)) 
    MY_LOGGER.debug('Sleeping for %d seconds', SLEEP_TIME)
    time.sleep(SLEEP_TIME)
    MY_LOGGER.debug('waking up again!')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
