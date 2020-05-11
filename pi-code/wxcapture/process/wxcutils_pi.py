#!/usr/bin/env python3
"""wxcapture utility code Pi specific functionality"""


# import libraries
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os
import time
import random
from rtlsdr import RtlSdr
import tweepy
from discord_webhook import DiscordWebhook, DiscordEmbed
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


def tweet_get_image_url(tgiu_config_path, tgiu_config_file):
    """get the url for the image in the last tweet"""
    tgiu_config = wxcutils.load_json(tgiu_config_path, tgiu_config_file)

    # authentication
    MY_UTIL_LOGGER.debug('Authenticating to Twitter API')
    tgiu_auth = tweepy.OAuthHandler(tgiu_config['consumer key'], tgiu_config['consumer secret'])
    tgiu_auth.set_access_token(tgiu_config['access token'], tgiu_config['access token secret'])

    # get api
    tgiu_api = tweepy.API(tgiu_auth)

    tgiu_twitter_handle = tgiu_config['tweet to'][1:]
    MY_UTIL_LOGGER.debug('last tweet for %s', tgiu_twitter_handle)

    tgiu_imagesfile = ''
    for tgiu_tweet in tweepy.Cursor(tgiu_api.user_timeline, tweet_mode='extended').items():
        if 'media' in tgiu_tweet.entities:
            for tgiu_image in tgiu_tweet.entities['media']:
                tgiu_imagesfile = str(tgiu_image['media_url'])
        break

    MY_UTIL_LOGGER.debug(tgiu_imagesfile)
    return tgiu_imagesfile


def webhooks(w_config_path, w_config_file, w_site_config_file, w_imagesfile, w_satellite,
             w_location, w_colour, w_elevation, w_duration, w_pass_start,
             w_channel_a, w_channel_b, w_description):
    """send data to webhooks as configured"""
    MY_UTIL_LOGGER.debug('webhooks called with %s %s %s %s %s %s %s %s %s %s %s %s %s',
                         w_config_path, w_config_file, w_site_config_file, w_imagesfile, w_satellite,
                         w_location, w_colour, w_elevation, w_duration, w_pass_start,
                         w_channel_a, w_channel_b, w_description)

    # convert w_colour from hex string to an int
    w_colour = int(w_colour, 16)

    w_config = wxcutils.load_json(w_config_path, w_config_file)
    w_site_config = wxcutils.load_json(w_config_path, w_site_config_file)

    MY_UTIL_LOGGER.debug('Iterate through webhooks')
    for w_row in w_config['webhooks']:
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
        w_embed.add_embed_field(name='Pass start', value='04:33:35 April 30  2020 (NZST)')
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


    def fix_pixel(fp_x, fp_y):
        """try to fix a pixel"""
        try_count = try_count_max
        fixed = False
        while True:
            try_count -= 1
            x_offset = 0
            if x_iterator <= 4:
                x_offset = random.randint(0, 2)
            elif x_iterator >= (image_width - 4):
                x_offset = random.randint(-2, 0)
            else:
                x_offset = random.randint(-2, 2)
            red_below, green_below, blue_below = image.getpixel((x_iterator + x_offset, y_iterator - 1))
            if red_below != 0 and green_below != 0 and blue_below != 0:
                image.putpixel((x_iterator, y_iterator), (red_below, green_below, blue_below))
                fixed == True
                break
            if try_count == 0:
                break
    

    image_height = 0
    image_width = 0
    image = Image.new('RGB', (1, 1), (0, 0, 0))
    min_pixel_thick_length = 30

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
    y_iterator = 0
    try_count_max = 5
    while y_iterator < image_height:
        if y_iterator%500 == 0:
            MY_UTIL_LOGGER.debug(y_iterator)
        x_iterator = 0
        while x_iterator < image_width:
            red, green, blue = image.getpixel((x_iterator, y_iterator))
            # MY_UTIL_LOGGER.debug('Pixel %d,%d = R%d G%d B%d', x_iterator, y_iterator, red, green, blue)
            # see if black is faulty
            if red == 0 and green == 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad black')
                fix_pixel(x_iterator, y_iterator)
            # see if cyan is faulty
            elif red == 0 and green != 0 and blue != 0:
                # MY_UTIL_LOGGER.debug('bad cyan')
                fix_pixel(x_iterator, y_iterator)
             # see if magenta is faulty
            elif red != 0 and green == 0 and blue != 0:
                # MY_UTIL_LOGGER.debug('bad magenta')
                fix_pixel(x_iterator, y_iterator)
            # see if yellow is faulty
            elif red != 0 and green != 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad yellow')
                fix_pixel(x_iterator, y_iterator)
            elif red != 0 and green == 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad red')
                fix_pixel(x_iterator, y_iterator)
            elif red == 0 and green != 0 and blue == 0:
                # MY_UTIL_LOGGER.debug('bad green')
                fix_pixel(x_iterator, y_iterator)
            elif red == 0 and green == 0 and blue != 0:
                # MY_UTIL_LOGGER.debug('bad blue')
                fix_pixel(x_iterator, y_iterator)

            x_iterator += 1
        y_iterator += 1

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

HOME = os.environ['HOME']
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_UTIL_LOGGER = get_logger('wxcutils_pi', HOME + '/wxcapture/process/logs/', 'wxcutils_pi.log')
