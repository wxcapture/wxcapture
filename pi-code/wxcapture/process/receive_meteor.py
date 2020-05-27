#!/usr/bin/env python3
"""capture and process METEOR satellite pass
create images plus pass web page"""

# capture and process METEOR satellite pass
# create images plus pass web page

# key code used for processing
# https://github.com/dbdexter-dev/meteor_demod
# https://github.com/artlav/meteor_decoder


# import libraries
import os
from os import path
import sys
import glob
import time
import subprocess
import wxcutils
import wxcutils_pi


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
    files_to_copy.append({'source path': OUTPUT_PATH,
                          'source file': FILENAME_BASE + '.dec',
                          'destination path': '', 'copied': 'no'})
    if CONFIG_INFO['save .wav files'] == 'yes':
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


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
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
    # timeout 600 rtl_fm -M raw -f 137.9M -s 768k -g 8 -p 0 |
    # sox -t raw -r 768k -c 2 -b 16 -e s - -t wav "meteor_a.wav" rate 192k
    if REPROCESS != 'Y':
        BIAS_T = get_bias_t()

        # Sleep until the required start time
        # to account for at scheduler starting up to 59 seconds early
        wxcutils_pi.sleep_until_start(float(START_EPOCH))

        MY_LOGGER.debug('Starting audio capture')
        wxcutils.run_cmd('timeout ' + DURATION + ' rtl_fm -d ' +
                         str(WX_SDR) + BIAS_T + ' -M raw -f ' + str(PASS_INFO['frequency']) +
                         'M -s 768k ' + GAIN_COMMAND +
                         ' -p 0 | sox -t raw -r 768k -c 2 -b 16 -e s - -t wav \"' +
                         AUDIO_PATH + FILENAME_BASE + '.wav\" rate 192k')
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
    wxcutils.run_cmd('echo yes | /usr/bin/meteor_demod -B ' + SYMBOL_RATE + ' ' + MODE + ' -o ' +
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

                # create full size .jpg of each .bmp
                MY_LOGGER.debug('create full size .jpg of each .bmp')
                # main
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE + '.bmp > ' + WORKING_PATH +
                                 FILENAME_BASE + '.jpg')
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE + '-cc.bmp.bmp > ' +
                                 WORKING_PATH + FILENAME_BASE + '-cc.jpg')
                # channels
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE + '_0.bmp > ' + WORKING_PATH +
                                 FILENAME_BASE + '_0.jpg')
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE + '_1.bmp > ' + WORKING_PATH +
                                 FILENAME_BASE + '_1.jpg')
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE + '_1.bmp > ' + WORKING_PATH +
                                 FILENAME_BASE + '_2.jpg')

                # Generate stretched version of the colour corrected .jpg
                MY_LOGGER.debug('Generate stretched version of the colour corrected .jpg')
                # main
                wxcutils.run_cmd('rectify-jpg ' + WORKING_PATH + FILENAME_BASE + '-cc.jpg')
                # channels
                wxcutils.run_cmd('rectify-jpg ' + WORKING_PATH + FILENAME_BASE + '_0.jpg')
                wxcutils.run_cmd('rectify-jpg ' + WORKING_PATH + FILENAME_BASE + '_1.jpg')
                wxcutils.run_cmd('rectify-jpg ' + WORKING_PATH + FILENAME_BASE + '_2.jpg')

                # move to image directory
                MY_LOGGER.debug('move to image directory')
                wxcutils.move_file(WORKING_PATH, FILENAME_BASE + '-cc-rectified.jpg',
                                   IMAGE_PATH, FILENAME_BASE + '-cc-rectified.jpg')
                wxcutils.move_file(WORKING_PATH, FILENAME_BASE + '_0-rectified.jpg',
                                   IMAGE_PATH, FILENAME_BASE + '_0-rectified.jpg')
                wxcutils.move_file(WORKING_PATH, FILENAME_BASE + '_1-rectified.jpg',
                                   IMAGE_PATH, FILENAME_BASE + '_1-rectified.jpg')
                wxcutils.move_file(WORKING_PATH, FILENAME_BASE + '_2-rectified.jpg',
                                   IMAGE_PATH, FILENAME_BASE + '_2-rectified.jpg')

                MY_LOGGER.debug('-' * 30)

                # create thumbnails
                # main
                MY_LOGGER.debug('create thumbnails')
                wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE +
                                 '-cc-rectified.jpg\" | pnmscale -xysize ' +
                                 IMAGE_OPTIONS['thumbnail size'] +
                                 ' | cjpeg -opti -progr -qual ' +
                                 IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                 IMAGE_PATH + FILENAME_BASE + '-cc-rectified-tn.jpg\"')
                # channels
                wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE +
                                 '_0-rectified.jpg\" | pnmscale -xysize ' +
                                 IMAGE_OPTIONS['thumbnail size'] +
                                 ' | cjpeg -opti -progr -qual ' +
                                 IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                 IMAGE_PATH + FILENAME_BASE + '_0-rectified-tn.jpg\"')
                wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE +
                                 '_1-rectified.jpg\" | pnmscale -xysize ' +
                                 IMAGE_OPTIONS['thumbnail size'] +
                                 ' | cjpeg -opti -progr -qual ' +
                                 IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                 IMAGE_PATH + FILENAME_BASE + '_1-rectified-tn.jpg\"')
                wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE +
                                 '_2-rectified.jpg\" | pnmscale -xysize ' +
                                 IMAGE_OPTIONS['thumbnail size'] +
                                 ' | cjpeg -opti -progr -qual ' +
                                 IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                 IMAGE_PATH + FILENAME_BASE + '_2-rectified-tn.jpg\"')

                # create a processed image
                wxcutils_pi.fix_image(WORKING_PATH + FILENAME_BASE + '-cc.bmp.bmp',
                                      WORKING_PATH + FILENAME_BASE + '-processed.bmp', 'N', 'Y')
                wxcutils.run_cmd('cjpeg -opti -progr -qual ' + IMAGE_OPTIONS['main image quality'] +
                                 ' ' + WORKING_PATH + FILENAME_BASE +  '-processed.bmp > ' +
                                 IMAGE_PATH + FILENAME_BASE + '-processed-tn.jpg')
                wxcutils.run_cmd('rectify-jpg ' + IMAGE_PATH + FILENAME_BASE + '-processed.jpg')
                wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE +
                                 '-processed-rectified.jpg\" | pnmscale -xysize ' +
                                 IMAGE_OPTIONS['thumbnail size'] +
                                 ' | cjpeg -opti -progr -qual ' +
                                 IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                 IMAGE_PATH + FILENAME_BASE + '-processed-rectified-tn.jpg\"')

                # move .dec file to output directory
                MY_LOGGER.debug('move .dec file to output directory')
                wxcutils.move_file(WORKING_PATH, FILENAME_BASE + '.dec',
                                   OUTPUT_PATH, FILENAME_BASE  + '.dec')

    # delete bmp and qpsk files
    # also intermediate jpg files
    # these will not error if the files do not exist
    MY_LOGGER.debug('delete intermediate files')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '*.bmp')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '.qpsk')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '.jpg')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '-cc.jpg')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '_0.jpg')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '_1.jpg')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '_2.jpg')

    # delete audio file?
    if CONFIG_INFO['save .wav files'] == 'no':
        MY_LOGGER.debug('Deleting .wav audio file')
        wxcutils.run_cmd('rm ' + AUDIO_PATH + FILENAME_BASE + '.wav')

    # ensure that we have at least one image created over the minimum size
    # no need to check for processed image since this is only created off the
    # main image, so it must exist for the processed image to be created
    MY_LOGGER.debug('check file size of main image')
    CREATE_PAGE = False
    try:
        FILE_SIZE = os.path.getsize(IMAGE_PATH + FILENAME_BASE +  '-cc-rectified.jpg')
        MY_LOGGER.debug('file size = %s', str(FILE_SIZE))
        if FILE_SIZE >= int(IMAGE_OPTIONS['image minimum']):
            MY_LOGGER.debug('Good file size for main image -> non-bad quality')
            CREATE_PAGE = True

        FILE_SIZE = os.path.getsize(IMAGE_PATH + FILENAME_BASE +  '_0-rectified.jpg')
        MY_LOGGER.debug('file size = %s', str(FILE_SIZE))
        if FILE_SIZE >= int(IMAGE_OPTIONS['image minimum']):
            MY_LOGGER.debug('Good file size for channel 0 image -> non-bad quality')
            CREATE_PAGE = True

        FILE_SIZE = os.path.getsize(IMAGE_PATH + FILENAME_BASE +  '_1-rectified.jpg')
        MY_LOGGER.debug('file size = %s', str(FILE_SIZE))
        if FILE_SIZE >= int(IMAGE_OPTIONS['image minimum']):
            MY_LOGGER.debug('Good file size for channel 1 image -> non-bad quality')
            CREATE_PAGE = True

        FILE_SIZE = os.path.getsize(IMAGE_PATH + FILENAME_BASE +  '_2-rectified.jpg')
        MY_LOGGER.debug('file size = %s', str(FILE_SIZE))
        if FILE_SIZE >= int(IMAGE_OPTIONS['image minimum']):
            MY_LOGGER.debug('Good file size for channel 2 image -> non-bad quality')
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

            if os.path.isfile(IMAGE_PATH + FILENAME_BASE + '-cc-rectified.jpg'):
                MY_LOGGER.debug('Adding image')
                MY_LOGGER.debug(os.path.getsize(IMAGE_PATH + FILENAME_BASE + '-cc-rectified.jpg'))
                html.write('<h3>Colour Image</h3>')
                html.write('<a href=\"images/' + FILENAME_BASE +
                           '-cc-rectified.jpg' + '\"><img src=\"images/' +
                           FILENAME_BASE + '-cc-rectified-tn.jpg' + '\"></a>')

            if os.path.isfile(IMAGE_PATH + FILENAME_BASE + '-processed-rectified.jpg'):
                MY_LOGGER.debug('Adding processed image')
                MY_LOGGER.debug(os.path.getsize(IMAGE_PATH + FILENAME_BASE +
                                                '-processed-rectified.jpg'))
                html.write('<h3>Processed Image</h3>')
                html.write('<a href=\"images/' + FILENAME_BASE +
                           '-processed-rectified.jpg' + '\"><img src=\"images/' +
                           FILENAME_BASE + '-processed-rectified-tn.jpg' + '\"></a>')

            if os.path.isfile(IMAGE_PATH + FILENAME_BASE + '_0-rectified.jpg'):
                MY_LOGGER.debug('Adding channel 0 image')
                MY_LOGGER.debug(os.path.getsize(IMAGE_PATH + FILENAME_BASE + '_0-rectified.jpg'))
                html.write('<h3>Channel 0 Image</h3>')
                html.write('<a href=\"images/' + FILENAME_BASE +
                           '_0-rectified.jpg' + '\"><img src=\"images/' +
                           FILENAME_BASE + '_0-rectified-tn.jpg' + '\"></a>')
            if os.path.isfile(IMAGE_PATH + FILENAME_BASE + '_1-rectified.jpg'):
                MY_LOGGER.debug('Adding channel 1 image')
                MY_LOGGER.debug(os.path.getsize(IMAGE_PATH + FILENAME_BASE + '_1-rectified.jpg'))
                html.write('<h3>Channel 1 Image</h3>')
                html.write('<a href=\"images/' + FILENAME_BASE +
                           '_1-rectified.jpg' + '\"><img src=\"images/' +
                           FILENAME_BASE + '_1-rectified-tn.jpg' + '\"></a>')
            if os.path.isfile(IMAGE_PATH + FILENAME_BASE + '_2-rectified.jpg'):
                MY_LOGGER.debug('Adding channel 2 image')
                MY_LOGGER.debug(os.path.getsize(IMAGE_PATH + FILENAME_BASE + '_2-rectified.jpg'))
                html.write('<h3>Channel 2 Image</h3>')
                html.write('<a href=\"images/' + FILENAME_BASE +
                           '_2-rectified.jpg' + '\"><img src=\"images/' +
                           FILENAME_BASE + '_2-rectified-tn.jpg' + '\"></a>')
            html.write('</body></html>')

        html.close()

    if CREATE_PAGE:
        # migrate files to destinations
        MY_LOGGER.debug('migrate files to destinations')
        migrate_files()
        # tweet?
        if IMAGE_OPTIONS['tweet'] == 'yes' and \
            int(MAX_ELEVATION) >= int(IMAGE_OPTIONS['tweet min elevation']):
            MY_LOGGER.debug('Tweeting pass')
            LOCATION_HASHTAGS = '#' + \
                CONFIG_INFO['Location'].replace(', ', ' #').replace(' ', '').replace('#', ' #')
            TWEET_TEXT = 'Latest weather satellite pass over ' + CONFIG_INFO['Location'] + \
                ' from ' + SATELLITE + ' on ' + PASS_INFO['start_date_local'] + \
                ' (Click on image to see detail) #weather ' + LOCATION_HASHTAGS
            # Must post the thumbnail as limit of 3MB for upload which full size image exceeds
            # change filename to select which image to webhook
            # normal -  '-cc-rectified-tn.jpg'
            # processes - '-processed-rectified-tn.jpg'
            TWEET_IMAGE = IMAGE_PATH + FILENAME_BASE + '-processed-tn.jpg'
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
        else:
            MY_LOGGER.debug('Tweeting not enabled')
        # discord webhook?
        if IMAGE_OPTIONS['discord webhooks'] == 'yes' and \
            int(MAX_ELEVATION) >= int(IMAGE_OPTIONS['discord min elevation']):
            # need to sleep a few minutes to enable the images to get to the web server
            # otherwise the image used by the webhook API will not be accessible when the
            # API is called
            MY_LOGGER.debug('Sleeping 5 minutes to allow the images to get to the web server')
            time.sleep(300)
            MY_LOGGER.debug('Sleep complete...')
            MY_LOGGER.debug('Webhooking pass')
            # Must post the thumbnail as limit of 3MB for upload which full size image exceeds
            FILENAME_BITS = FILENAME_BASE.split('-')
            # change filename to select which image to webhook
            # normal -  '-cc-rectified-tn.jpg'
            # processes - '-processed-rectified-tn.jpg'
            DISCORD_IMAGE = IMAGE_PATH + FILENAME_BASE + '-processed-rectified-tn.jpg'
            DISCORD_IMAGE_URL = CONFIG_INFO['website'] + '/' + FILENAME_BITS[0] + '/' + \
                FILENAME_BITS[1] + '/' + FILENAME_BITS[2] + '/images/' +  FILENAME_BASE + \
                '-processed-rectified-tn.jpg'
            MY_LOGGER.debug('discord_image_url = %s', DISCORD_IMAGE_URL)
            # only proceed if the image exists
            if path.exists(DISCORD_IMAGE):
                try:
                    wxcutils_pi.webhooks(CONFIG_PATH, 'config-discord.json', 'config.json',
                                         DISCORD_IMAGE_URL,
                                         SATELLITE, 'Pass over ' + CONFIG_INFO['Location'],
                                         IMAGE_OPTIONS['discord colour'],
                                         MAX_ELEVATION, DURATION, PASS_INFO['start_date_local'],
                                         '', '', 'Visible light image')
                except:
                    MY_LOGGER.critical('Discord exception handler: %s %s %s',
                                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            else:
                MY_LOGGER.debug('The image, %s, does not exist so skipping webhooking it.')
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
