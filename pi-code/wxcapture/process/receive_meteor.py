#!/usr/bin/env python3
"""capture and process METEOR satellite pass
create images plus pass web page"""

# capture and process METEOR satellite pass
# create images plus pass web page

# key code used for processing
# https://github.com/dbdexter-dev/meteor_demod
# https://github.com/artlav/meteor_decoder
# https://github.com/Digitelektro/MeteorDemod


# import libraries
import calendar
import glob
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from os import path

import cv2
import numpy as np
from PIL import Image, ImageOps

import wxcutils
import wxcutils_pi


def fix_image(fi_source, fi_destination, fi_image_fix):
    """remove noise from image"""

    def load_image(li_filename):
        """load an image file"""
        li_image = Image.open(li_filename)
        li_image_height = li_image.size[1]
        li_image_width = li_image.size[0]
        MY_LOGGER.debug('Loaded image %s height = %d width = %d type = %s',
                             li_filename, li_image_height, li_image_width, li_image.format)
        return li_image, li_image_height, li_image_width


    def save_image(si_filename):
        """save an image file"""
        MY_LOGGER.debug('Saving %s', si_filename)
        image.save(si_filename)
        MY_LOGGER.debug('Saved %s', si_filename)

    def new_value(nv_val1, nv_val2):
        """randomized combined value"""
        nv_new_value = ((nv_val1 + nv_val2) / 2) + random.randint(-5, 5)
        if nv_new_value < 0:
            nv_new_value = 0
        elif nv_new_value > 255:
            nv_new_value = 255
        return int(nv_new_value)

    image_height = 0
    image_width = 0
    image = Image.new('RGB', (1, 1), (0, 0, 0))

    MY_LOGGER.debug('Load image start')
    image, image_height, image_width = load_image(fi_source)
    MY_LOGGER.debug('Load image end')

    if fi_image_fix == 'Y':
        MY_LOGGER.debug('Image line removal start')
        y_iterator = 0
        while y_iterator < image_height:
            if y_iterator%500 == 0:
                MY_LOGGER.debug('line = %d', y_iterator)
            x_iterator = 0
            while x_iterator < image_width:
                red, green, blue = image.getpixel((x_iterator, y_iterator))
                # MY_LOGGER.debug('Pixel %d,%d = R%d G%d B%d', x_iterator, y_iterator, red, green, blue)
                # see if black is faulty
                if red == 0 and green == 0 and blue == 0:
                    # MY_LOGGER.debug('bad black')
                    pass
                # see if cyan is faulty
                elif red == 0 and green != 0 and blue != 0:
                    # MY_LOGGER.debug('bad cyan')
                    image.putpixel((x_iterator, y_iterator), (new_value(green, blue), green, blue))
                # see if magenta is faulty
                elif red != 0 and green == 0 and blue != 0:
                    # MY_LOGGER.debug('bad magenta')
                    image.putpixel((x_iterator, y_iterator), (red, new_value(red, blue), blue))
                # see if yellow is faulty
                elif red != 0 and green != 0 and blue == 0:
                    # MY_LOGGER.debug('bad yellow')
                    image.putpixel((x_iterator, y_iterator), (red, green, new_value(red, green)))
                elif red != 0 and green == 0 and blue == 0:
                    # MY_LOGGER.debug('good red')
                    image.putpixel((x_iterator, y_iterator), (red, new_value(red, red), new_value(red, red)))
                elif red == 0 and green != 0 and blue == 0:
                    # MY_LOGGER.debug('good green')
                    image.putpixel((x_iterator, y_iterator), (green, new_value(green, green), new_value(green, green)))
                elif red == 0 and green == 0 and blue != 0:
                    # MY_LOGGER.debug('good blue')
                    image.putpixel((x_iterator, y_iterator), (blue, new_value(blue, blue), new_value(blue, blue)))

                x_iterator += 1
            y_iterator += 1

        MY_LOGGER.debug('Image line removal finished')

    MY_LOGGER.debug('Save image start')
    save_image(fi_destination)
    MY_LOGGER.debug('Save image end')


def brand_image(bi_filename,
                bi_satellite,
                bi_max_elevation,
                bi_processing,
                bi_branding,
                bi_composite):
    """add image branding"""
    MY_LOGGER.debug('Adding image branding')
    MY_LOGGER.debug('filename = %s', bi_filename)
    MY_LOGGER.debug('satellite = %s', bi_satellite)
    MY_LOGGER.debug('max_elevation = %s', bi_max_elevation)
    MY_LOGGER.debug('processing = %s', bi_processing)
    MY_LOGGER.debug('branding = %s', bi_branding)
    if bi_composite:
        MY_LOGGER.debug('composite = True')
    else:
        MY_LOGGER.debug('composite = False')

    try:
        # load the image
        MY_LOGGER.debug('load image')
        input_image = cv2.imread(bi_filename)

        bi_text_size = 2
        border_size = 380
        y_inc = 60
        y_val = 0
        if '-tn.jpg' in bi_filename:
            MY_LOGGER.debug('Thumbnail detected')
            bi_text_size = 0.45
            border_size = 200
            y_inc = 30

        # image dimensions
        bi_height, bi_width = input_image.shape[:2]
        MY_LOGGER.debug('height = %d width = %d', bi_height, bi_width)

        # add the border to the top of the image
        output_image = cv2.copyMakeBorder(input_image, border_size, 0, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))

        # image dimensions
        bi_height, bi_width = output_image.shape[:2]
        MY_LOGGER.debug('new height = %d width = %d', bi_height, bi_width)

        # headline
        MY_LOGGER.debug('add headline')
        y_val += y_inc
        if bi_composite:
            output_image = cv2.putText(output_image, bi_satellite + ' - ' + ' composite', (20, y_val),
                                    cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)
        else:
            output_image = cv2.putText(output_image, bi_satellite + ' - ' + bi_max_elevation + ' degrees ' + PASS_INFO['max_elevation_direction'] + ' pass', (20, y_val),
                                    cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)

        y_val += y_inc
        output_image = cv2.putText(output_image, 'over ' + CONFIG_INFO['Location'], (20, y_val),
                                   cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)
        # UTC date
        year = PASS_INFO['startDate'][11:16]
        month = PASS_INFO['startDate'][7:10]
        day = PASS_INFO['startDate'][4:6]
        hour = PASS_INFO['startDate'][16:18]
        minute = PASS_INFO['startDate'][19:21]
        MY_LOGGER.debug('year = %s, month = %s, day = %s, hour = %s min = %s', year, month, day, hour, minute)
        y_val += y_inc
        output_image = cv2.putText(output_image, hour + ':' + minute + ' ' + day + '-' + month + '-' + year + ' UTC', (20, y_val),
                                   cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)

        # local date
        year = PASS_INFO['start_date_local'][11:16]
        month = PASS_INFO['start_date_local'][7:10]
        day = PASS_INFO['start_date_local'][4:6]
        hour = PASS_INFO['start_date_local'][16:18]
        minute = PASS_INFO['start_date_local'][19:21]
        MY_LOGGER.debug('year = %s, month = %s, day = %s, hour = %s min = %s', year, month, day, hour, minute)
        y_val += y_inc
        output_image = cv2.putText(output_image, hour + ':' + minute + ' ' + day + '-' + month + '-' + year + ' local', (20, y_val),
                                   cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)

        # pass info
        MY_LOGGER.debug('add pass info')
        y_val += y_inc
        output_image = cv2.putText(output_image, bi_processing, (20, y_val),
                                   cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)

        # kiwiweather.com
        y_val += y_inc
        output_image = cv2.putText(output_image, bi_branding, (20, y_val),
                                   cv2.FONT_HERSHEY_SIMPLEX, bi_text_size, (255, 255, 255), 2, cv2.LINE_AA)

        # add logo
        MY_LOGGER.debug('add logo')
        output_image[0:LOGO_IMAGE.shape[0], bi_width-LOGO_IMAGE.shape[1]:bi_width+LOGO_IMAGE.shape[1]] = LOGO_IMAGE

        # write out the new image
        MY_LOGGER.debug('write image')
        cv2.imwrite(bi_filename, output_image)
        MY_LOGGER.debug('brand_image completed')

    except Exception as err:
        MY_LOGGER.debug('Unexpected error creating brand_image : %s %s %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


def get_bias_t():
    """determine if we turn on the bias t"""
    command = ''
    if PASS_INFO['bias t'] == 'on':
        command = ' -T '
    MY_LOGGER.debug('bias t command = %s', command)
    return command


def migrate_files():
    """migrate files to server"""
    MY_LOGGER.debug('migrating files')
    files_to_copy = []
    files_to_copy.append({'source path': OUTPUT_PATH,
                          'source file': FILENAME_BASE + '.html',
                          'destination path': '', 'copied': 'no'})
    files_to_copy.append({'source path': OUTPUT_PATH,
                          'source file': FILENAME_BASE + '.txt',
                          'destination path': '', 'copied': 'no'})
    files_to_copy.append({'source path': OUTPUT_PATH,
                          'source file': FILENAME_BASE + '.json',
                          'destination path': '', 'copied': 'no'})
    files_to_copy.append({'source path': OUTPUT_PATH,
                          'source file': FILENAME_BASE + 'weather.tle',
                          'destination path': '', 'copied': 'no'})
    if CONFIG_INFO['save Meteor .wav files'] == 'yes':
        files_to_copy.append({'source path': AUDIO_PATH,
                              'source file': FILENAME_BASE + '.wav',
                              'destination path': 'audio/', 'copied': 'no'})
    for img_file in glob.glob(OUTPUT_PATH + 'images/' + FILENAME_BASE + '*.jpg'):
        img_path, img_filename = os.path.split(img_file)
        files_to_copy.append({'source path': img_path, 'source file': img_filename,
                              'destination path': 'images/', 'copied': 'no'})
    MY_LOGGER.debug('Files to copy = %s', files_to_copy)
    wxcutils.migrate_files(files_to_copy)
    MY_LOGGER.debug('Completed migrating files')


def webhook(w_enhancement):
    """webhook an image"""

    MY_LOGGER.debug('Webhooking pass for %s', w_enhancement)

    # sleep to minimise rate limit being hit
    # 20 seconds
    time.sleep(20)

    # Must post the thumbnail as limit of 3MB for upload which full size image exceeds
    filename_bits = FILENAME_BASE.split('-')
    # change filename to select which image to webhook
    # fixed - '-fixed-rectified-tn.jpg'
    DISCORD_IMAGE = IMAGE_PATH + FILENAME_BASE + '-' + w_enhancement + '-tn.jpg'

    # see if the file was created this pass
    if path.exists(DISCORD_IMAGE):
        MY_LOGGER.debug('File exists on this server - %s', DISCORD_IMAGE)

        DISCORD_IMAGE_URL = CONFIG_INFO['website'] + '/' + filename_bits[0] + '/' + \
            filename_bits[1] + '/' + filename_bits[2] + '/images/' +  FILENAME_BASE + \
            '-' + w_enhancement + '-tn.jpg'
        MY_LOGGER.debug('discord_image_url = %s', DISCORD_IMAGE_URL)
        # need to sleep a few minutes to enable the images to get to the web server
        # otherwise the image used by the webhook API will not be accessible when the
        # API is called
        MY_LOGGER.debug('Wait up to 15 minutes to allow the images to get to the web server')
        MAX_TIME = 15 * 60
        SLEEP_INTERVAL = 15
        TIMER = 0
        while TIMER <= MAX_TIME and not wxcutils.web_server_file_exists(DISCORD_IMAGE_URL):
            MY_LOGGER.debug('Current sleep time = %d', TIMER)
            MY_LOGGER.debug('Sleeping %d seconds', SLEEP_INTERVAL)
            time.sleep(SLEEP_INTERVAL)
            TIMER += SLEEP_INTERVAL
        MY_LOGGER.debug('Sleep complete...')

        # logging if the file exists on the webserver
        if wxcutils.web_server_file_exists(DISCORD_IMAGE_URL):
            MY_LOGGER.debug('url exists on webserver')
        else:
            MY_LOGGER.debug('url does NOT exist on webserver')
        if TIMER >= MAX_TIME:
            MY_LOGGER.debug('max time delay exceeded whilst waiting for image to arrive')

        # get the description
        for search, desc in IMAGE_OPTIONS['enhancements'].items():
            if search == w_enhancement:
                image_desc = desc

        # only proceed if the image exists on webserver
        if wxcutils.web_server_file_exists(DISCORD_IMAGE_URL):
            try:
                if 'composite' in branding_desc:
                    MY_LOGGER.debug('Composite image')
                    wxcutils_pi.webhooks(CONFIG_PATH, 'config-discord.json', 'config.json',
                                            DISCORD_IMAGE_URL,
                                            SATELLITE, 'Pass over ' + CONFIG_INFO['Location'],
                                            IMAGE_OPTIONS['discord colour'],
                                            'Composite', 'Composite', PASS_INFO['start_date_local'],
                                            '', '', image_desc)
                else:
                    MY_LOGGER.debug('Non-composite image')
                    wxcutils_pi.webhooks(CONFIG_PATH, 'config-discord.json', 'config.json',
                                            DISCORD_IMAGE_URL,
                                            SATELLITE, 'Pass over ' + CONFIG_INFO['Location'],
                                            IMAGE_OPTIONS['discord colour'],
                                            MAX_ELEVATION, DURATION, PASS_INFO['start_date_local'],
                                            '', '', image_desc)
            except:
                MY_LOGGER.critical('Discord exception handler: %s %s %s',
                                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        else:
            MY_LOGGER.debug('The image, %s, does not exist so skipping webhooking it.')
    else:
        MY_LOGGER.debug('File doesn\'t exist on this server - %s', DISCORD_IMAGE)


def tweet(t_enhancement):
    """tweet the image"""

    # sleep to minimise rate limit being hit
    # 5 seconds
    time.sleep(5)

    LOCATION_HASHTAGS = '#' + \
        CONFIG_INFO['Location'].replace(', ', ' #').replace(' ', '').replace('#', ' #')

    # get the description
    for search, desc in IMAGE_OPTIONS['enhancements'].items():
        if search == t_enhancement:
            image_desc = desc

    TWEET_TEXT = 'Latest ' + image_desc + ' weather satellite pass over ' + CONFIG_INFO['Location'] + \
        ' from ' + SATELLITE + ' on ' + PASS_INFO['start_date_local'] + \
        ' (Click on image to see detail) #weather ' + LOCATION_HASHTAGS
    # Must post the thumbnail as limit of 3MB for upload which full size image exceeds
    TWEET_IMAGE = IMAGE_PATH + FILENAME_BASE + '-' + t_enhancement + '-tn.jpg'
    # only proceed if the image exists
    if path.exists(TWEET_IMAGE):
        try:
            wxcutils_pi.tweet_text_image(CONFIG_PATH, 'config-twitter.json',
                                         TWEET_TEXT, TWEET_IMAGE)
        except:
            MY_LOGGER.critical('Tweet exception handler: %s %s %s',
                                sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        MY_LOGGER.debug('Tweeted!')
    else:
        MY_LOGGER.debug('The image, %s, does not exist so skipping tweeting it.',
                        TWEET_IMAGE)


def add_image(ai_title, ai_file, ai_thumb):
    """add in the HTML for an image if it exists"""
    MY_LOGGER.debug('Adding title %s for %s image', ai_title, ai_file)
    if os.path.isfile(IMAGE_PATH + FILENAME_BASE + ai_file):
        MY_LOGGER.debug('File exists, so adding it...')
        MY_LOGGER.debug(os.path.getsize(IMAGE_PATH + FILENAME_BASE + ai_file))
        html.write('<h3>' + ai_title + '</h3>')
        html.write('<a href=\"images/' + FILENAME_BASE +
                   ai_file + '\"><img src=\"images/' +
                   FILENAME_BASE + ai_thumb + '\"></a>')
    else:
        MY_LOGGER.debug('File does not exist, so skiping adding it...')
        


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
MD_WORKING_PATH = WORKING_PATH + 'mdtemp/'
CONFIG_PATH = CODE_PATH + 'config/'
AUDIO_PATH = APP_PATH + 'audio/'

# start logging
MODULE = 'receive_meteor'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')
MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('CODE_PATH = %s', CODE_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('OUTPUT_PATH = %s', OUTPUT_PATH)
MY_LOGGER.debug('IMAGE_PATH = %s', IMAGE_PATH)
MY_LOGGER.debug('WORKING_PATH = %s', WORKING_PATH)
MY_LOGGER.debug('MD_WORKING_PATH = %s', MD_WORKING_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)
MY_LOGGER.debug('AUDIO_PATH = %s', AUDIO_PATH)

try:
    try:
        # extract parameters
        SATELLITE_TYPE = sys.argv[1]
        SATELLITE_NUM = sys.argv[2]
        SATELLITE = SATELLITE_TYPE + ' ' + SATELLITE_NUM
        START_EPOCH = sys.argv[3]
        DURATION = sys.argv[4]
        MAX_ELEVATION = sys.argv[5]
        REPROCESS = sys.argv[6]
    except IndexError as exc:
        MY_LOGGER.critical('Exception whilst parsing command line parameters: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        # re-throw it as this is fatal
        raise

    MY_LOGGER.debug('satellite = %s', SATELLITE)
    MY_LOGGER.debug('START_EPOCH = %s', str(START_EPOCH))
    MY_LOGGER.debug('DURATION = %s', str(DURATION))
    MY_LOGGER.debug('MAX_ELEVATION = %s', str(MAX_ELEVATION))
    MY_LOGGER.debug('REPROCESS = %s', REPROCESS)

    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    # load satellites
    SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'satellites.json')

    # load image options
    IMAGE_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-METEOR.json')

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-2]

    # load logo image once
    MY_LOGGER.debug('load logo')
    LOGO_IMAGE = cv2.imread(CONFIG_PATH + 'logo.jpg')

    # create filename base
    FILENAME_BASE = wxcutils.epoch_to_utc(START_EPOCH, '%Y-%m-%d-%H-%M-%S') + \
        '-' + SATELLITE.replace(' ', '_')
    MY_LOGGER.debug('FILENAME_BASE = %s', FILENAME_BASE)

    # load pass information
    PASS_INFO = wxcutils.load_json(OUTPUT_PATH, FILENAME_BASE + '.json')
    MY_LOGGER.debug(PASS_INFO)

    # validate tle files exist
    wxcutils.validate_tle(WORKING_PATH)

    # to enable REPROCESSing using the original tle file, rename it to match the FILENAME_BASE
    wxcutils.copy_file(WORKING_PATH + 'weather.tle', OUTPUT_PATH +
                       FILENAME_BASE + 'weather.tle')

    # write out process information
    with open(OUTPUT_PATH + FILENAME_BASE + '.txt', 'w') as txt:
        txt.write('./receive_meteor.py ' + sys.argv[1] + ' ' + sys.argv[2] +
                  ' ' + sys.argv[3] + ' ' + sys.argv[4] + ' ' + sys.argv[5] +
                  ' ' + 'Y')
    txt.close()

    # determine the device index based on the serial number
    MY_LOGGER.debug('SDR serial number = %s', PASS_INFO['serial number'])
    WX_SDR = wxcutils_pi.get_sdr_device(PASS_INFO['serial number'])
    MY_LOGGER.debug('SDR device ID = %d', WX_SDR)

    GAIN_COMMAND, GAIN_DESCRIPTION, GAIN_VALUE = wxcutils_pi.get_gain(IMAGE_OPTIONS,
                                                                      str(MAX_ELEVATION))

    # capture pass to wav file
    # timeout 600 rtl_fm -M raw -f 137.9M -s 130k -g 8 -p 0 |
    # sox -t raw -r 130k -c 2 -b 16 -e s - -t wav "meteor_a.wav" rate 96k
    if REPROCESS != 'Y':
        BIAS_T = get_bias_t()

        # Sleep until the required start time
        # to account for at scheduler starting up to 59 seconds early
        wxcutils_pi.sleep_until_start(float(START_EPOCH))

        MY_LOGGER.debug('Starting audio capture')
        wxcutils.run_cmd('timeout ' + DURATION + ' rtl_fm -d ' +
                         str(WX_SDR) + BIAS_T + ' -M raw -f ' + str(PASS_INFO['frequency']) +
                         'M -s 130k ' + GAIN_COMMAND +
                         ' -p 0 | sox -t raw -r 130k -c 2 -b 16 -e s - -t wav \"' +
                         AUDIO_PATH + FILENAME_BASE + '.wav\" rate 128k')
        if os.path.isfile(AUDIO_PATH + FILENAME_BASE + '.wav'):
            MY_LOGGER.debug('Audio file created')
        else:
            MY_LOGGER.debug('Audio file NOT created')
    else:
        MY_LOGGER.debug('Reprocessing original .wav file')

    MY_LOGGER.debug('-' * 30)

    # assume we don't get a valid page, but confirm if we do
    CREATE_PAGE = False

    # Demodulate .wav to QPSK
    MY_LOGGER.debug('Demodulate .wav to QPSK')
    SYMBOL_RATE = ' -r ' + str(PASS_INFO['meteor symbol rate'])
    MODE = ' -m ' + PASS_INFO['meteor mode']
    wxcutils.run_cmd('echo yes | /usr/local/bin/meteor_demod -B ' + SYMBOL_RATE + ' ' + MODE + ' -o ' +
                     WORKING_PATH + FILENAME_BASE + '.qpsk ' + AUDIO_PATH + FILENAME_BASE + '.wav')
    MY_LOGGER.debug('-' * 30)

    if not os.path.isfile(WORKING_PATH + FILENAME_BASE + '.qpsk'):
        MY_LOGGER.debug('No .qpsk file created, unable to continue to decode pass')
    else:
        MY_LOGGER.debug('A .qpsk file was created, continuing decoding')

        # Keep original file timestamp
        MY_LOGGER.debug('Keep original file timestamp')
        wxcutils.run_cmd('touch -r ' + AUDIO_PATH + FILENAME_BASE + '.wav ' + WORKING_PATH +
                         FILENAME_BASE + '.qpsk')
        MY_LOGGER.debug('-' * 30)

        # Decode QPSK to .dec and .bmp (non-colour corrected)
        MY_LOGGER.debug('Decode QPSK to .dec and .bmp (non-colour corrected)')
        wxcutils.run_cmd('/usr/local/bin/medet_arm ' + WORKING_PATH + FILENAME_BASE + '.qpsk '
                         + WORKING_PATH + FILENAME_BASE + ' -S -cd')
        MY_LOGGER.debug('-' * 30)

        if not os.path.isfile(WORKING_PATH + FILENAME_BASE + '.dec'):
            MY_LOGGER.debug('No .dec file created, unable to continue to decode pass')
        else:
            MY_LOGGER.debug('A .dec file was created, continuing decoding')

            # Generate colour corrected .bmp
            # active APIDs are at:
            # http://happysat.nl/Meteor/html/Meteor_Status.html
            MY_LOGGER.debug('Generate colour corrected .bmp')
            wxcutils.run_cmd('/usr/local/bin/medet_arm ' + WORKING_PATH + FILENAME_BASE + '.dec ' +
                             WORKING_PATH + FILENAME_BASE + '-cc.bmp -r 66 -g 65 -b 64 -d')
            MY_LOGGER.debug('-' * 30)

            # note that the bmp file created has the extension .bmp.bmp!
            if not os.path.isfile(WORKING_PATH + FILENAME_BASE + '-cc.bmp.bmp'):
                MY_LOGGER.debug('No -cc.bmp file created, unable to continue to generate images')
            else:
                MY_LOGGER.debug('A -cc.bmp file was created, continuing generating images')

                # northbound pass, need to rotate image 180 degrees
                if PASS_INFO['direction'] == 'Northbound':
                    MY_LOGGER.debug('Northbound pass - must rotate image')
                    wxcutils.run_cmd('convert ' + WORKING_PATH + FILENAME_BASE + '-cc.bmp.bmp' +
                                     ' -rotate 180 ' + WORKING_PATH + FILENAME_BASE + '-cc.bmp.bmp')
                else:
                    MY_LOGGER.debug('Southbound pass - no rotation required')

                # fix image to remove noice
                fix_image(WORKING_PATH + FILENAME_BASE + '-cc.bmp.bmp',
                          WORKING_PATH + FILENAME_BASE + '-fixed.bmp',
                          'Y')

                # create full size .jpg of each .bmp
                MY_LOGGER.debug('create full size .jpg of each .bmp')
                # main
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE + '-fixed.bmp > ' +
                                 WORKING_PATH + FILENAME_BASE + '-fixed.jpg')

                # Generate stretched version of the colour corrected .jpg
                MY_LOGGER.debug('Generate stretched version of the colour corrected .jpg')
                # main
                # wxcutils.run_cmd('rectify-jpg ' + WORKING_PATH + FILENAME_BASE + '-cc.jpg')
                wxcutils.run_cmd('rectify-jpg ' + WORKING_PATH + FILENAME_BASE + '-fixed.jpg')

                # move to image directory
                MY_LOGGER.debug('move to image directory')
                wxcutils.move_file(WORKING_PATH, FILENAME_BASE + '-fixed-rectified.jpg',
                                   IMAGE_PATH, FILENAME_BASE + '-fixed-rectified.jpg')

                MY_LOGGER.debug('-' * 30)

                # create thumbnails
                # main
                MY_LOGGER.debug('create thumbnails')
                wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE +
                                 '-fixed-rectified.jpg\" | pnmscale -xysize ' +
                                 IMAGE_OPTIONS['thumbnail size'] +
                                 ' | cjpeg -opti -progr -qual ' +
                                 IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                 IMAGE_PATH + FILENAME_BASE + '-fixed-rectified-tn.jpg\"')

                # start of MeteorDemod processing

                # remove any created images older than 6 hours
                MY_LOGGER.debug('remove any created images older than 6 hours')
                file_list = os.listdir(MD_WORKING_PATH)
                epoch_seconds_now = time.time()
                max_age = 6 * 60 * 60
                for filename in file_list:
                    if epoch_seconds_now - os.path.getmtime(MD_WORKING_PATH + filename) >= max_age:
                        # delete the file
                        wxcutils.run_cmd('rm ' + MD_WORKING_PATH + filename)

                # create images with meteor_demod using qspk file
                MY_LOGGER.debug('create images with meteor_demod using qspk file')
                MY_LOGGER.debug('*' * 40)
                MY_LOGGER.debug('*' * 40)
                DATE_STRING_DMY = wxcutils.epoch_to_utc(START_EPOCH, '%d-%m-%Y')
                MY_LOGGER.debug('DATE_STRING_DMY = %s', DATE_STRING_DMY)
                DATE_STRING_YMD = wxcutils.epoch_to_utc(START_EPOCH, '%Y-%m-%-d')
                MY_LOGGER.debug('DATE_STRING_YMD = %s', DATE_STRING_YMD)

                wxcutils.run_cmd('meteordemod -i ' + WORKING_PATH + FILENAME_BASE + '.qpsk -t ' +
                                 OUTPUT_PATH + FILENAME_BASE + 'weather.tle -f jpg -d ' +
                                 DATE_STRING_DMY + ' -o ' + MD_WORKING_PATH)

                # copy and rename files to the output directory
                file_list = os.listdir(MD_WORKING_PATH)
                for filename in file_list:
                    if filename[:11] == 'equidistant':
                        base, ext = filename.split('.')
                        base_bits = base.split('_')
                        MY_LOGGER.debug('filename = %s, base = %s, ext = %s, base_bits = %s, len(base_bits) = %d', filename, base, ext, base_bits, len(base_bits))
                        if len(base_bits) == 5 and base_bits[3] == 'composite':
                            brand_search = base_bits[0] + '-' + base_bits[2] + '-' + base_bits[3] + '-' + base_bits[4]
                            new_filename = FILENAME_BASE + '-' + brand_search + '.' + ext
                        elif len(base_bits) == 4 and base_bits[3] == 'composite':
                            brand_search = base_bits[0] + '-' + base_bits[2] + '-' + base_bits[3]
                            new_filename = FILENAME_BASE + '-' + brand_search + '.' + ext
                        elif len(base_bits) == 4:
                            brand_search = base_bits[0] + '-' + base_bits[1] + '-' + base_bits[2]
                            new_filename = FILENAME_BASE + '-' + brand_search + '.' + ext
                        elif len(base_bits) == 3:
                            brand_search = base_bits[0] + '-' + base_bits[1]
                            new_filename = FILENAME_BASE + '-' + brand_search + '.' + ext
                        else:
                            MY_LOGGER.error('Unandled length %s for %s', len(base_bits), base_bits)

                        for search, desc in IMAGE_OPTIONS['enhancements'].items():
                            if search == brand_search:
                                branding_desc = desc

                        MY_LOGGER.debug('Old filename = %s, new filename = %s', filename, new_filename)

                        # move file to new location
                        MY_LOGGER.debug('Move files to working directory')
                        wxcutils.copy_file(MD_WORKING_PATH + filename, WORKING_PATH + new_filename)

                        # add branding
                        MY_LOGGER.debug('Add branding to image')
                        for search, desc in IMAGE_OPTIONS['enhancements'].items():
                            if search == brand_search:
                                branding_desc = desc
                        MY_LOGGER.debug('brand search = %s, description = %s', brand_search, branding_desc)

                        if 'composite' in branding_desc:
                            MY_LOGGER.debug('Composite image')
                            contains_composite = True
                        else:
                            MY_LOGGER.debug('Non-composite image')
                            contains_composite = False
                        
                        brand_image(WORKING_PATH + new_filename,
                                    SATELLITE, MAX_ELEVATION,
                                    branding_desc,
                                    IMAGE_OPTIONS['Branding'], contains_composite)

                        # generate thumbnail
                        name, ext = new_filename.split('.')
                        wxcutils.run_cmd('djpeg \"' + WORKING_PATH + new_filename +
                                        '\" | pnmscale -xysize ' +
                                        IMAGE_OPTIONS['thumbnail size'] +
                                        ' | cjpeg -opti -progr -qual ' +
                                        IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                        IMAGE_PATH + name + '-tn.jpg\"')

                        # move file to output location
                        MY_LOGGER.debug('move to output directory')
                        wxcutils.move_file(WORKING_PATH, new_filename, IMAGE_PATH, new_filename)

                MY_LOGGER.debug('*' * 40)
                MY_LOGGER.debug('*' * 40)

    # delete bmp and qpsk files
    # also intermediate jpg files
    # these will not error if the files do not exist
    MY_LOGGER.debug('delete intermediate files')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '*.bmp')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '.qpsk')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '-fixed.jpg')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '.dec')

    # delete audio file?
    if CONFIG_INFO['save Meteor .wav files'] == 'no':
        MY_LOGGER.debug('Deleting .wav audio file')
        wxcutils.run_cmd('rm ' + AUDIO_PATH + FILENAME_BASE + '.wav')

    # ensure that we have at least one image created over the minimum size
    # no need to check for processed image since this is only created off the
    # main image, so it must exist for the processed image to be created
    MY_LOGGER.debug('check file size of main image')
    CREATE_PAGE = False
    try:
        FILE_SIZE = os.path.getsize(IMAGE_PATH + FILENAME_BASE +  '-fixed-rectified.jpg')
        MY_LOGGER.debug('file size = %s', str(FILE_SIZE))
        if FILE_SIZE >= int(IMAGE_OPTIONS['image minimum']):
            MY_LOGGER.debug('Good file size for main fixed image -> non-bad quality')
            CREATE_PAGE = True

    except Exception as err:
        MY_LOGGER.debug('Unexpected error validating norm image file size: %s %s %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

    if CREATE_PAGE:
        # build web page for pass
        MY_LOGGER.debug('build web page for pass')
        with open(OUTPUT_PATH + FILENAME_BASE + '.html', 'w') as html:
            html.write('<!DOCTYPE html>')
            html.write('<html lang=\"en\"><head>')
            html.write('<meta charset=\"UTF-8\">'
                       '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                       '<meta name=\"description\" content=\"Satellite pass capture page for NOAA / Meteor / International Space Station (ISS) SSTV / Amsat (Amateur Satellites)\">'
                       '<meta name=\"keywords\" content=\"' + CONFIG_INFO['webpage keywords'] + '\">'
                       '<meta name=\"author\" content=\"WxCapture\">')
            html.write('<title>Satellite Pass Images</title></head>')
            html.write('<body><h2>' + SATELLITE + '</h2>')
            html.write('<table><tr><td>')
            html.write('<ul>')
            html.write('<li>Max pass elevation - ' + MAX_ELEVATION + '&deg; '
                       + PASS_INFO['max_elevation_direction'] + '</li>')
            html.write('<li>Pass direction - ' + PASS_INFO['direction'] + '</li>')
            html.write('<li>Pass start (' + PASS_INFO['timezone'] + ') - ' +
                       PASS_INFO['start_date_local'] + '</li>')
            html.write('<li>Pass end (' + PASS_INFO['timezone'] + ') - ' +
                       PASS_INFO['end_date_local'] + '</li>')
            html.write('<li>Pass start (UTC) - ' + PASS_INFO['startDate'] + '</li>')
            html.write('<li>Pass end (UTC) - ' + PASS_INFO['endDate'] + '</li>')
            html.write('<li>Pass duration - ' + str(PASS_INFO['duration']) +
                       ' seconds' + '</li>')
            html.write('<li>Orbit - ' + PASS_INFO['orbit'] + '</li>')
            html.write('<li>SDR type - ' + PASS_INFO['sdr type'] + ' (' +
                       PASS_INFO['chipset'] + ')</li>')
            html.write('<li>SDR gain - ' + GAIN_VALUE + 'dB</li>')
            html.write('<li>Antenna - ' + PASS_INFO['antenna'] + ' (' +
                       PASS_INFO['centre frequency'] + ')</li>')
            html.write('<li>Frequency range - ' + PASS_INFO['frequency range'] + '</li>')
            html.write('<li>Modules - ' + PASS_INFO['modules'] + '</li>')
            html.write('</ul></td><td>')
            html.write('<img src=\"images/' + FILENAME_BASE + '-plot.png\">')
            html.write('</td></tr></table>')
            html.write('<h2>Colour Corrected Image</h2>')

            html.write('<p>Click on the image to get the full size image.</p>')

            MY_LOGGER.debug('FILENAME_BASE = %s', FILENAME_BASE)

            add_image('Processed Standard Image', '-fixed-rectified.jpg', '-fixed-rectified-tn.jpg')

            add_image('Equidistant projection 125', '-equidistant-125.jpg', '-equidistant-125-tn.jpg')
            add_image('Equidistant projection 125 - composite', '-equidistant-125-composite.jpg', '-equidistant-125-composite-tn.jpg')

            add_image('Equidistant projection 221', '-equidistant-221.jpg', '-equidistant-221-tn.jpg')
            add_image('Equidistant projection 221 - composite', '-equidistant-221-composite.jpg', '-equidistant-221-composite-tn.jpg')

            add_image('Equidistant projection infrared', '-equidistant-IR.jpg', '-equidistant-IR-tn.jpg')
            add_image('Equidistant projection infrared - composite', '-equidistant-IR-composite.jpg', '-equidistant-IR-composite-tn.jpg')

            add_image('Equidistant projection 125 rain', '-equidistant-rain-125.jpg', '-equidistant-rain-125-tn.jpg')
            add_image('Equidistant projection 125 rain- composite', '-equidistant-rain-125-composite.jpg', '-equidistant-rain-125-composite-tn.jpg')

            add_image('Equidistant projection 221 rain', '-equidistant-rain-221.jpg', '-equidistant-rain-221-tn.jpg')
            add_image('Equidistant projection 221 rain - composite', '-equidistant-rain-221-composite.jpg', '-equidistant-rain-221-composite-tn.jpg')

            add_image('Equidistant projection infrared rain', '-equidistant-rain-IR.jpg', '-equidistant-rain-IR-tn.jpg')
            add_image('Equidistant projection infrared rain - composite', '-equidistant-rain-IR-composite.jpg', '-equidistant-rain-IR-composite-tn.jpg')

            add_image('Equidistant projection 68 - composite', '-equidistant-68-composite.jpg', '-equidistant-68-composite-tn.jpg')
            add_image('Equidistant projection 68 rain - composite', '-equidistant-68-rain-composite.jpg', '-equidistant-68-rain-composite-tn.jpg')

            add_image('Equidistant projection thermal', '-equidistant-thermal.jpg', '-equidistant-thermal-tn.jpg')
            add_image('Equidistant projection thermal - composite', '-equidistant-thermal-composite.jpg', '-equidistant-thermal-composite-tn.jpg')

            html.write('</body></html>')

        html.close()

    if CREATE_PAGE:
        # add branding to pages
        brand_image(IMAGE_PATH + FILENAME_BASE + '-fixed-rectified.jpg',
                    SATELLITE, MAX_ELEVATION,
                    'Processed full colour',
                    IMAGE_OPTIONS['Branding'], False)
        brand_image(IMAGE_PATH + FILENAME_BASE + '-fixed-rectified-tn.jpg',
                    SATELLITE, MAX_ELEVATION,
                    'Processed full colour',
                    IMAGE_OPTIONS['Branding'], False)

        # migrate files to destinations
        MY_LOGGER.debug('migrate files to destinations')
        migrate_files()

        # tweet?
        if IMAGE_OPTIONS['tweet'] == 'yes' and \
            int(MAX_ELEVATION) >= int(IMAGE_OPTIONS['tweet min elevation']):
            MY_LOGGER.debug('Tweeting pass')
            tweet('fixed-rectified')

            tweet('equidistant-125')
            tweet('equidistant-125-composite')

            tweet('equidistant-221')
            tweet('equidistant-221-composite')

            tweet('equidistant-IR')
            tweet('equidistant-IR-composite')

            tweet('equidistant-rain-125')
            tweet('equidistant-rain-125-composite')

            tweet('equidistant-rain-221')
            tweet('equidistant-rain-221-composite')

            tweet('equidistant-thermal')
            tweet('equidistant-thermal-composite')


        else:
            MY_LOGGER.debug('Tweeting not enabled')

        # discord webhook?
        if IMAGE_OPTIONS['discord webhooks'] == 'yes' and \
            int(MAX_ELEVATION) >= int(IMAGE_OPTIONS['discord min elevation']):

            webhook('fixed-rectified')

            webhook('equidistant-125')
            webhook('equidistant-125-composite')

            webhook('equidistant-221')
            webhook('equidistant-221-composite')

            webhook('equidistant-IR')
            webhook('equidistant-IR-composite')

            webhook('equidistant-rain-125')
            webhook('equidistant-rain-125-composite')

            webhook('equidistant-rain-221')
            webhook('equidistant-rain-221-composite')

            webhook('equidistant-thermal')
            webhook('equidistant-thermal-composite')

        else:
            MY_LOGGER.debug('Webhooking not enabled')

    else:
        MY_LOGGER.debug('Page not created due to image size')
        MY_LOGGER.debug('Deleting any objects created')
        wxcutils.run_cmd('rm ' + OUTPUT_PATH + FILENAME_BASE + '.html')
        wxcutils.run_cmd('rm ' + IMAGE_PATH + FILENAME_BASE + '*.*')
        wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '*.*')
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
