#!/usr/bin/env python3
"""tweet Sanchez images"""


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


def upload_file_chunked(uf_config_path, uf_config_file, uf_file):
    """upload a file to the Twitter API"""

    # code based on https://gist.github.com/jcipriano/e506b81a6062307c5189

    def check_status(r):
        MY_LOGGER.debug('check status')
        if r.status_code < 200 or r.status_code > 299:
            MY_LOGGER.error('ERROR status')
            MY_LOGGER.debug('status = %s', r.status_code)
            MY_LOGGER.debug('text = %s', r.text)
            sys.exit(0)
        MY_LOGGER.debug('check status OK')

    # get the Twitter API config
    uf_config = wxcutils.load_json(uf_config_path, uf_config_file)

    # start API
    MY_LOGGER.debug('Start the API')
    twitter = TwitterAPI(uf_config['consumer key'], uf_config['consumer secret'],
                         uf_config['access token'], uf_config['access token secret'])

    bytes_sent = 0
    total_bytes = os.path.getsize(uf_file)
    file = open(uf_file, 'rb')
    MY_LOGGER.debug('file = %s, size = %d', uf_file, total_bytes)

    # init
    MY_LOGGER.debug('Init')
    r = twitter.request('media/upload', {'command':'INIT', 'media_type':'video/mp4', 'total_bytes':total_bytes})
    check_status(r)

    media_id = r.json()['media_id']
    segment_id = 0

    MY_LOGGER.debug('Chunking')
    # start chucked upload
    while bytes_sent < total_bytes:
        chunk = file.read(1*1024*1024)
        
        # upload chunk of byets (1MB max)
        r = twitter.request('media/upload', {'command':'APPEND', 'media_id':media_id, 'segment_index':segment_id}, {'media':chunk})
        check_status(r)
        segment_id = segment_id + 1
        bytes_sent = file.tell()

    MY_LOGGER.debug('Chunking complete')

    # finalize the upload
    MY_LOGGER.debug('Finalize')
    r = twitter.request('media/upload', {'command':'FINALIZE', 'media_id':media_id})
    check_status(r)

    MY_LOGGER.debug('media_id = %s', media_id)
    return media_id


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
            tt_media_id = upload_file_chunked(tt_config_path, tt_config_file, tt_file)
            
            # send tweet
            MY_LOGGER.debug('Sending tweet with text = %s, image = %s', tt_text, tt_file)
            tt_status = tt_api.update_status(status=tt_text, media_ids=[tt_media_id])
        else:
            MY_LOGGER.debug('Unknown file type - can''t upload')

    MY_LOGGER.debug('Tweet sent with status = %s', tt_status)


def get_tweet_text(image):
    """pick a random image text line from what is configured"""

    main_text = 'Satellite image'
    main_hashtag = ''
    base_hashtag = ''
    see_more = ''
    for key, value in TWEETTEXT.items():
        # MY_LOGGER.debug('key = %s', key)

        if key == 'images':
            for img in TWEETTEXT[key]:
                if image == img['Filename']:
                    # select a random main text
                    random_pick = random.randint(1, len(img['Textlines'])) - 1
                    MY_LOGGER.debug('pick = %d, text = %s', random_pick, img['Textlines'][random_pick])
                    main_text = img['Textlines'][random_pick]
                    # select a random main hashtag
                    random_pick = random.randint(1, len(img['hashtags'])) - 1
                    MY_LOGGER.debug('pick = %d, text = %s', random_pick, img['hashtags'][random_pick])
                    main_hashtag = img['hashtags'][random_pick]

        # select a random base hashtag
        if key == 'base hashtags':
            # MY_LOGGER.debug('key = %s, value = %s', key, value)
            random_pick = random.randint(1, len(value)) - 1
            MY_LOGGER.debug('pick = %d, text = %s', random_pick, value[random_pick])
            base_hashtag = value[random_pick]

        # select a random see more
        if key == 'see more':
            # MY_LOGGER.debug('key = %s, value = %s', key, value)
            random_pick = random.randint(1, len(value)) - 1
            MY_LOGGER.debug('pick = %d, text = %s', random_pick, value[random_pick])
            see_more = value[random_pick]

    return main_text + ' ' + main_hashtag + ' ' + base_hashtag + ' ' + see_more


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

# loop through tweets to tweet
for key, value in TWEETS.items():
    # MY_LOGGER.debug('key = %s, value = %s', key, value)
    if key == 'Tweets':
        for tweet in value:
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

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
