#!/usr/bin/env python3
"""wxcapture utility code Pi specific functionality"""


# import libraries
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os
import time
from rtlsdr import RtlSdr
import tweepy
from discord_webhook import DiscordWebhook, DiscordEmbed
import cv2
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
    logger.setLevel(wxcutils.get_logger_level())
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


def webhooks(w_config_path, w_config_file, w_site_config_file, w_imagesfile, w_satellite,
             w_location, w_colour, w_elevation, w_duration, w_pass_start,
             w_channel_a, w_channel_b, w_description):
    """send data to webhooks as configured"""
    MY_UTIL_LOGGER.debug('webhooks called with %s %s %s %s %s %s %s %s %s %s %s %s %s',
                         w_config_path, w_config_file, w_site_config_file,
                         w_imagesfile, w_satellite,
                         w_location, w_colour, w_elevation, w_duration, w_pass_start,
                         w_channel_a, w_channel_b, w_description)

    # convert w_colour from hex string to an int
    w_colour = int(w_colour, 16)

    w_config = wxcutils.load_json(w_config_path, w_config_file)
    w_site_config = wxcutils.load_json(w_config_path, w_site_config_file)

    MY_UTIL_LOGGER.debug('Iterate through webhooks')
    for w_row in w_config['webhooks']:
        MY_UTIL_LOGGER.debug('webhook last 3 chars = %s', w_row[len(w_row) - 3:])
        w_webhook = DiscordWebhook(url=w_row)

        # create embed object for webhook
        w_embed = DiscordEmbed(title=w_satellite, description=w_location, color=w_colour)

        # set image
        w_embed.set_image(url=w_imagesfile)

        # set footer
        w_embed.set_footer(text=w_config['footer'].replace('[SITE]', w_site_config['website']))

        # add fields to embed
        w_embed.add_embed_field(name='Satellite', value=':satellite_orbital:' + w_satellite)
        w_embed.add_embed_field(name='Max Elevation', value=(w_elevation + '°'))
        w_embed.add_embed_field(name='Duration', value=(w_duration + ' seconds'))
        w_embed.add_embed_field(name='Pass start', value=w_pass_start)
        if w_channel_a != '':
            w_embed.add_embed_field(name='Channel A', value=w_channel_a)
        if w_channel_b != '':
            w_embed.add_embed_field(name='Channel B', value=w_channel_b)
        if w_description != '':
            w_embed.add_embed_field(name='Pass Description', value=w_description)

        # add embed object to webhook
        w_webhook.add_embed(w_embed)

        w_response = w_webhook.execute()
        MY_UTIL_LOGGER.debug('response = %s', w_response)


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


def get_gain(gg_config, gg_max_elevation):
    """determine the gain setting, either auto or defined"""
    MY_UTIL_LOGGER.debug('get_gain %s', gg_max_elevation)
    command = ''
    description = ''
    gain_value = ''
    if gg_config['auto gain'] == 'yes':
        description = 'Automatic gain control'
        gain_value = 'auto'
    else:
        if int(gg_max_elevation) <= 20:
            gain_value = gg_config['gain 20']
            command = ' -g ' + gain_value
            description = 'Gain set to ' + gain_value
        elif int(gg_max_elevation) <= 30:
            gain_value = gg_config['gain 30']
            command = ' -g ' + gain_value
            description = 'Gain set to ' + gain_value
        elif int(gg_max_elevation) <= 60:
            gain_value = gg_config['gain 60']
            command = ' -g ' + gain_value
            description = 'Gain set to ' + gain_value
        elif int(gg_max_elevation) <= 90:
            gain_value = gg_config['gain 90']
            command = ' -g ' + gain_value
            description = 'Gain set to ' + gain_value

    MY_UTIL_LOGGER.debug('gain value = %s', gain_value)
    MY_UTIL_LOGGER.debug('gain command = %s', command)
    MY_UTIL_LOGGER.debug('description = %s', description)
    return command, description, gain_value


def clahe_process(cp_in_path, cp_in_file, cp_out_path, cp_out_file):
    """clahe process the file using OpenCV library"""
    def clahe(in_img):
        """do clahe create processing on image"""
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(in_img)

    def do_clahe_img(in_img):
        """do clahe merge processing on image"""
        b_chn, g_chn, r_chn = cv2.split(in_img)
        return cv2.merge((clahe(b_chn), clahe(g_chn), clahe(r_chn)))

    MY_UTIL_LOGGER.debug('clahe_process %s %s %s %s', cp_in_path, cp_in_file,
                         cp_out_path, cp_out_file)
    MY_UTIL_LOGGER.debug('process image')
    cp_out_img = do_clahe_img(cv2.imread(cp_in_path + cp_in_file))
    MY_UTIL_LOGGER.debug('write new image')
    cv2.imwrite(cp_out_path + cp_out_file, cp_out_img)
    MY_UTIL_LOGGER.debug('write image complete')


HOME = os.environ['HOME']
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_UTIL_LOGGER = get_logger('wxcutils_pi', HOME + '/wxcapture/process/logs/', 'wxcutils_pi.log')
