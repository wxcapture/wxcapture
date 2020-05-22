#!/usr/bin/env python3
"""capture and process NOAA satellite pass
create images plus pass web page"""


# import libraries
import os
from os import path
import sys
import glob
import random
import time
import subprocess
from subprocess import Popen, PIPE
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
    files_to_copy.append({'source path': OUTPUT_PATH, 'source file': FILENAME_BASE + '.html', 'destination path': '', 'copied': 'no'})
    files_to_copy.append({'source path': OUTPUT_PATH, 'source file': FILENAME_BASE + '.txt', 'destination path': '', 'copied': 'no'})
    files_to_copy.append({'source path': OUTPUT_PATH, 'source file': FILENAME_BASE + '.json', 'destination path': '', 'copied': 'no'})
    files_to_copy.append({'source path': OUTPUT_PATH, 'source file': FILENAME_BASE + 'weather.tle', 'destination path': '', 'copied': 'no'})
    if CONFIG_INFO['save .wav files'] == 'yes':
        files_to_copy.append({'source path': AUDIO_PATH, 'source file': FILENAME_BASE + '.wav', 'destination path': 'audio/', 'copied': 'no'})
    for img_file in glob.glob(OUTPUT_PATH + 'images/' + FILENAME_BASE + '*.jpg'):
        img_path, img_filename = os.path.split(img_file)
        files_to_copy.append({'source path': img_path, 'source file': img_filename, 'destination path': 'images/', 'copied': 'no'})
    for img_file in glob.glob(OUTPUT_PATH + 'images/' + FILENAME_BASE + '*.png'):
        img_path, img_filename = os.path.split(img_file)
        files_to_copy.append({'source path': img_path, 'source file': img_filename, 'destination path': 'images/', 'copied': 'no'})

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
MODULE = 'receive_noaa'
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
    MY_LOGGER.debug('duration = %s', str(DURATION))
    MY_LOGGER.debug('MAX_ELEVATION = %s', str(MAX_ELEVATION))
    MY_LOGGER.debug('REPROCESS = %s', REPROCESS)

    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    # load satellites
    SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'satellites.json')

    # load image options
    IMAGE_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-NOAA.json')

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]

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
    wxcutils.copy_file(WORKING_PATH + 'weather.tle', OUTPUT_PATH + FILENAME_BASE + 'weather.tle')

    # write out process information
    with open(OUTPUT_PATH + FILENAME_BASE + '.txt', 'w') as txt:
        txt.write('./receive_noaa.py ' + sys.argv[1] + ' ' + sys.argv[2] + ' '
                  + sys.argv[3] + ' ' + sys.argv[4] + ' ' + sys.argv[5] + ' '
                  + 'Y')
    txt.close()

    # capture pass to wav file
    GAIN_COMMAND, GAIN_DESCRIPTION, GAIN_VALUE = wxcutils_pi.get_gain(IMAGE_OPTIONS, str(MAX_ELEVATION))
    MY_LOGGER.debug('Frequency = %s', str(PASS_INFO['frequency']))
    MY_LOGGER.debug('Gain command = %s', str(GAIN_COMMAND))
    MY_LOGGER.debug('Sample rate = %s', IMAGE_OPTIONS['sample rate'])
    MY_LOGGER.debug('Duration = %s', DURATION)

    # determine the device index based on the serial number
    MY_LOGGER.debug('SDR serial number = %s', PASS_INFO['serial number'])
    WX_SDR = wxcutils_pi.get_sdr_device(PASS_INFO['serial number'])
    MY_LOGGER.debug('SDR device ID = %d', WX_SDR)

    BIAS_T = get_bias_t()

    if REPROCESS != 'Y':
        # Sleep until the required start time
        # to account for at scheduler starting up to 59 seconds early
        wxcutils_pi.sleep_until_start(float(START_EPOCH))

        MY_LOGGER.debug('Starting audio capture')
        wxcutils.run_cmd('timeout ' + DURATION + ' rtl_fm -d ' +
                         str(WX_SDR) + BIAS_T +' -f ' + str(PASS_INFO['frequency']) + 'M '
                         + GAIN_COMMAND +
                         ' -s ' + IMAGE_OPTIONS['sample rate'] +
                         ' -E deemp -F 9 - | sox -t raw -e signed -c 1 -b 16 -r '
                         + IMAGE_OPTIONS['sample rate'] + ' - \"' + AUDIO_PATH +
                         FILENAME_BASE + '.wav\" rate 11025')
        MY_LOGGER.debug('Finished audio capture')
        if os.path.isfile(AUDIO_PATH + FILENAME_BASE + '.wav'):
            MY_LOGGER.debug('Audio file created')
        else:
            MY_LOGGER.debug('Audio file NOT created')
    else:
        MY_LOGGER.debug('Reprocessing original .wav file')

    MY_LOGGER.debug('-' * 30)

    # create map file
    # offset of pass duration / 2 for the pass start time is to avoid
    # errors from wxmap which will only create
    # the map file if the satellite is in view over the configured
    # location at the time specified
    # hence the additional time to ensure it is
    START_TIME = int(START_EPOCH) + (int(DURATION) * 0.5)
    MY_LOGGER.debug('wxmap start time = %d (seconds since unix epoch) duration = %s (seconds)',
                    START_TIME, str(DURATION))
    wxcutils.run_cmd('/usr/local/bin/wxmap -T \"' + SATELLITE + '\" -H '
                     + WORKING_PATH + 'weather.tle -p ' +
                     str(IMAGE_OPTIONS['Population']) + ' -l 0 -o -M 1 ' +
                     str(START_TIME) + ' ' + IMAGE_PATH + FILENAME_BASE +
                     '-map.png')

    KEEP_PAGE = True
    # build web page for pass
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
        html.write('</ul></td><td></table>')
        html.write('<img src=\"images/' + FILENAME_BASE + '-plot.png\">')
        html.write('</td></tr>')
        html.write('<table border = 1>')
        html.write('<tr><th>Click on thumbnail for full size '
                   'image</th><th>Description</th></tr>')

        # generate images
        ENHANCEMENTS = IMAGE_OPTIONS['enhancements']
        for key in sorted(ENHANCEMENTS.keys()):
            MY_LOGGER.debug(key + ' ' + ENHANCEMENTS[key]['active'] + ' ' + \
                ENHANCEMENTS[key]['description'] + ' ' + \
                ENHANCEMENTS[key]['filename'] + ' ' + \
                ENHANCEMENTS[key]['options'])

            if ENHANCEMENTS[key]['active'] == 'yes':
                removeImage = False
                MY_LOGGER.debug(key)
                MY_LOGGER.debug(' %s', ENHANCEMENTS[key]['description'])
                MY_LOGGER.debug(' %s', ENHANCEMENTS[key]['options'])
                # create standard image enhancements
                options = ENHANCEMENTS[key]['options'].split()
                optionsLength = len(options)
                if optionsLength == 0:
                    cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                                 IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                                 '-A', '-Q ' + IMAGE_OPTIONS['main image quality'],
                                 '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                 AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH
                                 + FILENAME_BASE + '-' +
                                 ENHANCEMENTS[key]['filename'] + '.jpg'],
                                stdout=PIPE, stderr=PIPE)
                    MY_LOGGER.debug('optionsLength = 0 %s %s %s %s %s %s %s %s %s %s %s %s', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['main image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
                elif optionsLength == 1:
                    cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                                 IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                                 '-A', '-Q ' + IMAGE_OPTIONS['main image quality'],
                                 '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                 options[0], options[1], AUDIO_PATH +
                                 FILENAME_BASE + '.wav', IMAGE_PATH +
                                 FILENAME_BASE + '-' +
                                 ENHANCEMENTS[key]['filename'] + '.jpg'],
                                stdout=PIPE, stderr=PIPE)
                    MY_LOGGER.debug('optionsLength = 1 %s %s %s %s %s %s %s %s %s %s %s %s %s', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['main image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
                elif optionsLength == 2:
                    cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                                 IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                                 '-A', '-Q ' + IMAGE_OPTIONS['main image quality'],
                                 '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                 options[0], options[1], AUDIO_PATH +
                                 FILENAME_BASE + '.wav', IMAGE_PATH +
                                 FILENAME_BASE + '-' +
                                 ENHANCEMENTS[key]['filename'] + '.jpg'],
                                stdout=PIPE, stderr=PIPE)
                    MY_LOGGER.debug('optionsLength = 2 %s %s %s %s %s %s %s %s %s %s %s %s %s %s', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['main image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
                elif optionsLength == 3:
                    cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                                 IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                                 '-A', '-Q ' + IMAGE_OPTIONS['main image quality'],
                                 '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                 options[0], options[1], options[2],
                                 AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH +
                                 FILENAME_BASE + '-' +
                                 ENHANCEMENTS[key]['filename'] + '.jpg'],
                                stdout=PIPE, stderr=PIPE)
                    MY_LOGGER.debug('optionsLength = 3 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['main image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], options[2], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
                elif optionsLength == 4:
                    cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                                 IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                                 '-A', '-Q ' + IMAGE_OPTIONS['main image quality'],
                                 '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                 options[0], options[1], options[2], options[3],
                                 AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH +
                                 FILENAME_BASE + '-' +
                                 ENHANCEMENTS[key]['filename'] + '.jpg'],
                                stdout=PIPE, stderr=PIPE)
                    MY_LOGGER.debug('optionsLength = 4 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['main image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], options[2], options[3], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
                else:
                    MY_LOGGER.debug('unhandled options length - need to update code to process this')
                    cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                                 IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A',
                                 '-Q ' + IMAGE_OPTIONS['main image quality'],
                                 '-m',
                                 IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH +
                                 FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE +
                                 '-' + ENHANCEMENTS[key]['filename'] + '.jpg'],
                                stdout=PIPE, stderr=PIPE)
                    MY_LOGGER.debug('optionsLength = %s %s %s %s %s %s %s %s %s %s %s %s %s', str(optionsLength), '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['main image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
                stdout, stderr = cmd.communicate()

                MY_LOGGER.debug('===out')
                MY_LOGGER.debug(stdout)
                MY_LOGGER.debug('===')
                # extract gain info and check for errors
                lines = stdout.decode('utf-8').splitlines()

                # add temperature scale if applicable
                if ENHANCEMENTS[key]['scale'] != 'no':
                    MY_LOGGER.debug('Need to add temperature scale')
                    MY_LOGGER.debug('Finding image height')
                    image_file = IMAGE_PATH + FILENAME_BASE + '-' + \
                        ENHANCEMENTS[key]['filename'] + '.jpg'
                    cmd = Popen(['identify', '-format', '\"%h\"', IMAGE_PATH,
                                 image_file], stdout=PIPE, stderr=PIPE)
                    stdout, stderr = cmd.communicate()
                    height = stdout.decode('utf-8').replace('\"', '')
                    MY_LOGGER.debug('height = %s', height)
                    y_offset = int((int(height) - 320) / 2)
                    MY_LOGGER.debug('y_offset = %s', str(y_offset))
                    if y_offset >= 0:
                        MY_LOGGER.debug('adding temperature scale')
                        scales_file = CODE_PATH + 'scales/' + ENHANCEMENTS[key]['filename'] + '.png'
                        MY_LOGGER.debug('scales_file = %s', scales_file)
                        MY_LOGGER.debug('image_file = %s', image_file)
                        cmd = Popen(['composite', '-geometry', '+0+' +
                                     str(y_offset), scales_file, image_file,
                                     image_file], stdout=PIPE, stderr=PIPE)
                        stdout, stderr = cmd.communicate()
                        MY_LOGGER.debug('completed adding temperature scale')
                    else:
                        MY_LOGGER.debug('unable to add temperature scale as iamge too small')

                # decode output info
                channelA = 'information not present'
                channelB = 'information not present'
                gain = 'information not present'

                for row in lines:
                    if 'Gain' in row:
                        gain = row
                        if GAIN_VALUE == 'auto':
                            gain = gain + \
                                'dB image processing / automatic gain SDR'
                        else:
                            gain = gain + ' image processing / ' + \
                                GAIN_DESCRIPTION + ' dB gain SDR'
                    if 'Channel A' in row:
                        channelA = row
                    if 'Channel B' in row:
                        channelB = row
                    if 'wxtoimg: warning: enhancement ignored' in row:
                        removeImage = True
                        MY_LOGGER.debug('Unable to create enhancement ' +
                                        ENHANCEMENTS[key]['description'] + ' - ' + row)
                        # remove image created
                        wxcutils.run_cmd('rm ' + IMAGE_PATH + FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.jpg')

                    if 'wxtoimg: warning: solar elevation' in row:
                        removeImage = True
                        MY_LOGGER.debug('Unable to create enhancement - solar elevation ' +
                                        ENHANCEMENTS[key]['description'] + ' - ' + row)
                        # remove image created
                        wxcutils.run_cmd('rm ' + IMAGE_PATH + FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.jpg')

                MY_LOGGER.debug(gain + ' ' + channelA + ' ' + channelB)

                # create thumbnail and write html table content - only if we image is good
                if not removeImage:
                    wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + FILENAME_BASE + '-' +
                                     ENHANCEMENTS[key]['filename'] +
                                     '.jpg\" | pnmscale -xysize ' +
                                     IMAGE_OPTIONS['thumbnail size'] +
                                     ' | cjpeg -opti -progr -qual ' +
                                     IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                     IMAGE_PATH + FILENAME_BASE + '-' +
                                     ENHANCEMENTS[key]['filename'] + '-tn.jpg\"')
                    html.write('<tr><td><a href=\"images/' + FILENAME_BASE
                               + '-' + ENHANCEMENTS[key]['filename'] +
                               '.jpg' + '\"><img src=\"images/' +
                               FILENAME_BASE + '-' +
                               ENHANCEMENTS[key]['filename'] +
                               '-tn.jpg' + '\"></a></td><td>')
                    html.write('<ul><li>' +
                               ENHANCEMENTS[key]['description'] +
                               '</li><li>' + channelA + '</li><li>' +
                               channelB + '</li><li>' + gain + '</li></ul>')
                    html.write('</td></tr>')

                # update the pass json with NOAA data
                PASS_INFO['NOAA Channel A'] = channelA
                PASS_INFO['NOAA Channel B'] = channelB
                PASS_INFO['NOAA Image Gain'] = gain

                # create the projection info, if enabled
                MY_LOGGER.debug('Projection creation?')
                MY_LOGGER.debug('ENHANCEMENTS[key] = %s', ENHANCEMENTS[key])
                try:
                    if ENHANCEMENTS[key]['projection'] == 'yes':
                        MY_LOGGER.debug('Creating png to be projected - %s', ENHANCEMENTS[key]['projection'])
                        if optionsLength == 0:
                            cmd = Popen(['/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A',
                                         '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                         AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH
                                         + FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.png'],
                                        stdout=PIPE, stderr=PIPE)
                            MY_LOGGER.debug('optionsLength = 0 %s %s %s %s %s %s %s  %s %s %s', '/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A', '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png')
                        elif optionsLength == 1:
                            cmd = Popen(['/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A',
                                         '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                         options[0], options[1], AUDIO_PATH +
                                         FILENAME_BASE + '.wav', IMAGE_PATH +
                                         FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.png'],
                                        stdout=PIPE, stderr=PIPE)
                            MY_LOGGER.debug('optionsLength = 1 %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A', '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png')
                        elif optionsLength == 2:
                            cmd = Popen(['/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A',
                                         '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                         options[0], options[1], AUDIO_PATH +
                                         FILENAME_BASE + '.wav', IMAGE_PATH +
                                         FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.png'],
                                        stdout=PIPE, stderr=PIPE)
                            MY_LOGGER.debug('optionsLength = 2 %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A', '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png')
                        elif optionsLength == 3:
                            cmd = Popen(['/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A',
                                         '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                         options[0], options[1], options[2],
                                         AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH +
                                         FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.png'],
                                        stdout=PIPE, stderr=PIPE)
                            MY_LOGGER.debug('optionsLength = 3 %s %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A', '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], options[2], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png')
                        elif optionsLength == 4:
                            cmd = Popen(['/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A',
                                         '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                                         options[0], options[1], options[2], options[3],
                                         AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH +
                                         FILENAME_BASE + '-' +
                                         ENHANCEMENTS[key]['filename'] + '.png'],
                                        stdout=PIPE, stderr=PIPE)
                            MY_LOGGER.debug('optionsLength = 4 %s %s %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A', '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], options[2], options[3], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png')
                        else:
                            MY_LOGGER.debug('unhandled options length - need to update code to process this')
                            cmd = Popen(['/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A',
                                         '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH +
                                         FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE +
                                         '-' + ENHANCEMENTS[key]['filename'] + '.jppngg'],
                                        stdout=PIPE, stderr=PIPE)
                            MY_LOGGER.debug('optionsLength = %s %s %s %s %s %s %s %s %s %s %s ', str(optionsLength), '/usr/local/bin/wxtoimg', '-c', '-E', '-o', '-I', '-A', '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png')

                        stdout, stderr = cmd.communicate()
                        MY_LOGGER.debug('===out')
                        MY_LOGGER.debug(stdout)
                        MY_LOGGER.debug('===')
                        MY_LOGGER.debug('Creating projection')
                        longitude = float(CONFIG_INFO['GPS location NS'].split(' ')[0])
                        if CONFIG_INFO['GPS location NS'].split(' ')[1] == 'S':
                            longitude *= -1
                        latitude = float(CONFIG_INFO['GPS location EW'].split(' ')[0])
                        if CONFIG_INFO['GPS location NS'].split(' ')[1] == 'W':
                            latitude *= -1

                        cmd = Popen(['/usr/local/bin/wxproj', '-o', '-' + IMAGE_OPTIONS['projection N/S type'], '-p', IMAGE_OPTIONS['projection type'],
                                     '-l', str(longitude), '-m', str(latitude), '-b', IMAGE_OPTIONS['projection bounding box'], '-s', '1',
                                     IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png',
                                     IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-proj.png'],
                                    stdout=PIPE, stderr=PIPE)
                        MY_LOGGER.debug('Projection %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s', '/usr/local/bin/wxproj',
                                        '-o', '-' + IMAGE_OPTIONS['projection N/S type'], '-p', IMAGE_OPTIONS['projection type'],
                                        '-l', str(longitude), '-m', str(latitude), '-b', IMAGE_OPTIONS['projection bounding box'], '-s', '1',
                                        IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.png',
                                        IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-proj.png')
                        stdout, stderr = cmd.communicate()
                        MY_LOGGER.debug('===out')
                        MY_LOGGER.debug(stdout)
                        MY_LOGGER.debug('===')
                        cmd = Popen(['convert', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-proj.png',
                                     '-transparent', '\'rgb(0,0,0)\'',
                                     IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-proj-trans.png'],
                                    stdout=PIPE, stderr=PIPE)
                        MY_LOGGER.debug('Projection transparency %s %s %s %s %s',
                                        'convert', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-proj.png',
                                        '-transparent', '\'rgb(0,0,0)\'',
                                        IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-proj-trans.png')
                        stdout, stderr = cmd.communicate()
                        MY_LOGGER.debug('===out')
                        MY_LOGGER.debug(stdout)
                        MY_LOGGER.debug('===')
                        MY_LOGGER.debug('find pass(es) to include, if 2+ exist')
                        MY_TIME = ''
                        MY_PASS_MERIDIAN = ''
                        MY_SATELLITE = ''
                        PASSES = wxcutils.load_json(WORKING_PATH, 'passes_today.json')

                        for sat_pass in PASSES:
                            if sat_pass['sat type'] == 'NOAA':
                                MY_LOGGER.debug('%s %s %s %s %s', sat_pass['satellite'], sat_pass['time'], sat_pass['pass meridian'], sat_pass['start_date_local'], sat_pass['filename_base'])
                                if sat_pass['filename_base'] == FILENAME_BASE:
                                    MY_TIME = int(sat_pass['time'])
                                    MY_PASS_MERIDIAN = sat_pass['pass meridian']
                                    MY_SATELLITE = sat_pass['satellite']
                        MY_LOGGER.debug('MY_PASS_MERIDIAN = %s', MY_PASS_MERIDIAN)
                        MY_LOGGER.debug('MY_TIME = %d', MY_TIME)
                        MY_LOGGER.debug('MY_SATELLITE = %s', MY_SATELLITE)

                        MY_LOGGER.debug('Prior passes to include - same satellite')
                        FILE_LIST = ''
                        FILE_SAME_DESC = 'Passes from this morning for the ' + MY_SATELLITE + ' satellite are:<ul>'
                        if MY_PASS_MERIDIAN == 'pm':
                            FILE_SAME_DESC = 'Passes from this evening for the ' + MY_SATELLITE + ' satellite are:<ul>'
                        FILE_SAME_COUNT = 0
                        for sat_pass in PASSES:
                            if sat_pass['sat type'] == 'NOAA' and sat_pass['pass meridian'] == MY_PASS_MERIDIAN and int(sat_pass['time']) <= MY_TIME and sat_pass['satellite'] == MY_SATELLITE:
                                MY_LOGGER.debug('%s %s %s %s %s', sat_pass['satellite'], sat_pass['time'], sat_pass['pass meridian'], sat_pass['start_date_local'], sat_pass['filename_base'])
                                FILE_NAME = IMAGE_PATH + sat_pass['filename_base'] + '-' + ENHANCEMENTS[key]['filename'] + '-proj-trans.png'
                                if os.path.isfile(FILE_NAME):
                                    FILE_LIST += FILE_NAME + ' '
                                    FILE_SAME_DESC += '<li>' + sat_pass['satellite'] + ' - ' + sat_pass['start_date_local'] + '</li>'
                                    FILE_SAME_COUNT += 1
                                else:
                                    MY_LOGGER.debug('Can not find transparent projection file - %s', FILE_NAME)
                        if FILE_SAME_COUNT > 1:
                            MY_LOGGER.debug('Files for projection = %d', FILE_SAME_COUNT)
                            FILE_SAME_DESC += '</ul>'
                            MY_LOGGER.debug(FILE_SAME_DESC)
                            MY_LOGGER.debug('Files in projection = %d', FILE_SAME_COUNT)
                            PROJ_BASE = FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '-'  + MY_PASS_MERIDIAN + '-' + MY_SATELLITE.replace(' ', '-')
                            wxcutils.run_cmd('convert ' + FILE_LIST +  ' -evaluate-sequence Max -trim ' + IMAGE_PATH + PROJ_BASE + '.png')

                            if ENHANCEMENTS[key]['scale'] != 'no':
                                MY_LOGGER.debug('Need to add temperature scale')
                                MY_LOGGER.debug('Finding image height')
                                image_file = IMAGE_PATH + PROJ_BASE + '.png'
                                cmd = Popen(['identify', '-format', '\"%h\"', IMAGE_PATH,
                                             image_file], stdout=PIPE, stderr=PIPE)
                                stdout, stderr = cmd.communicate()
                                height = stdout.decode('utf-8').replace('\"', '')
                                MY_LOGGER.debug('height = %s', height)
                                y_offset = int((int(height) - 320) / 2)
                                MY_LOGGER.debug('y_offset = %s', str(y_offset))
                                if y_offset >= 0:
                                    MY_LOGGER.debug('adding temperature scale')
                                    scales_file = CODE_PATH + 'scales/' + ENHANCEMENTS[key]['filename'] + '.png'
                                    MY_LOGGER.debug('scales_file = %s', scales_file)
                                    MY_LOGGER.debug('image_file = %s', image_file)
                                    cmd = Popen(['composite', '-geometry', '+0+' +
                                                 str(y_offset), scales_file, image_file,
                                                 image_file], stdout=PIPE, stderr=PIPE)
                                    stdout, stderr = cmd.communicate()
                                    MY_LOGGER.debug('completed adding temperature scale')
                                else:
                                    MY_LOGGER.debug('unable to add temperature scale as iamge too small')

                            wxcutils.run_cmd('convert -quality ' + IMAGE_OPTIONS['main image quality'] + ' ' + IMAGE_PATH + PROJ_BASE + '.png ' + IMAGE_PATH + PROJ_BASE + '.jpg')
                            wxcutils.run_cmd('rm ' + IMAGE_PATH + PROJ_BASE + '.png')
                            # generate thumbnail
                            wxcutils.run_cmd('djpeg \"' + IMAGE_PATH + PROJ_BASE +
                                             '.jpg\" | pnmscale -xysize ' +
                                             IMAGE_OPTIONS['thumbnail size'] +
                                             ' | cjpeg -opti -progr -qual ' +
                                             IMAGE_OPTIONS['thumbnail quality'] + ' > \"' +
                                             IMAGE_PATH + PROJ_BASE + '-tn.jpg\"')
                            # also include html code
                            html.write('<tr><td><a href=\"images/' + PROJ_BASE +
                                       '.jpg' + '\"><img src=\"images/' +
                                       PROJ_BASE + '-tn.jpg' + '\"></a></td><td>')
                            html.write(FILE_SAME_DESC)
                            html.write('</td></tr>')
                        else:
                            MY_LOGGER.debug('Not enough files (%s) to make a valid projection', FILE_SAME_COUNT)
                    else:
                        MY_LOGGER.debug('Projections not enabled for %s', ENHANCEMENTS[key]['projection'])

                except Exception as err:
                    MY_LOGGER.debug('Unexpected error creating projections : %s %s %s',
                                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


        try:
            NORM_FILE_SIZE = os.path.getsize(IMAGE_PATH + FILENAME_BASE + '-norm.jpg')
            MY_LOGGER.debug('norm_file_size = %s', str(NORM_FILE_SIZE))
            if NORM_FILE_SIZE < int(IMAGE_OPTIONS['image minimum']):
                MY_LOGGER.debug('Low file size for norm image -> bad quality')
                KEEP_PAGE = False
            else:
                MY_LOGGER.debug('Good file size for norm image -> non-bad quality')
                KEEP_PAGE = True
        except Exception as err:
            MY_LOGGER.debug('Unexpected error validating norm image file size : %s %s %s',
                            sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

        html.write('</table></body></html>')

    html.close()

    # save updated pass info json file
    MY_LOGGER.debug('Saving pass info to json file')
    wxcutils.save_json(OUTPUT_PATH, FILENAME_BASE + '.json', PASS_INFO)

    # delete audio file?
    if CONFIG_INFO['save .wav files'] == 'no':
        MY_LOGGER.debug('Deleting .wav audio file')
        wxcutils.run_cmd('rm ' + AUDIO_PATH + FILENAME_BASE + '.wav')

    if IMAGE_OPTIONS['tweet'] == 'yes' and int(MAX_ELEVATION) >= int(IMAGE_OPTIONS['tweet min elevation']):

        # create a copy of the tweet groups
        # validate if image for each enhancement in the tweet groups exists, if not, remove as an option
        # if no options exist in tweet group, remove the group
        TWEET_GROUPS = IMAGE_OPTIONS['tweet groups']
        MY_LOGGER.debug('removing options where there is no file')
        for tweet_group in TWEET_GROUPS:
            for tweet_option in tweet_group:
                for row in tweet_group[tweet_option]:
                    if not path.exists(IMAGE_PATH + FILENAME_BASE + '-' + row['type'] + '.jpg'):
                        tweet_group[tweet_option].remove(row)

        MY_LOGGER.debug('Tweeting pass(s)')
        LOCATION_HASHTAGS = '#' + CONFIG_INFO['Location'].replace(', ', ' #').replace(' ', '').replace('#', ' #')
        for tweet_group in TWEET_GROUPS:
            for tweet_option in tweet_group:
                random_pick = random.randint(1, len(tweet_group[tweet_option])) - 1
                enhancement = tweet_group[tweet_option][random_pick]['type']
                tweet_text = tweet_group[tweet_option][random_pick]['text']
                pass_description = ''
                for enhancement_group in IMAGE_OPTIONS['enhancements']:
                    if IMAGE_OPTIONS['enhancements'][enhancement_group]['filename'] == enhancement:
                        pass_description = IMAGE_OPTIONS['enhancements'][enhancement_group]['description']
                MY_LOGGER.debug('enahancement = %s', enhancement)
                MY_LOGGER.debug('initial tweet_text = %s', tweet_text)
                MY_LOGGER.debug('pass_description = %s', pass_description)

                # replace tags with variable values
                tweet_text = tweet_text.replace('[LOCATION]', CONFIG_INFO['Location'])
                tweet_text = tweet_text.replace('[PASS START]', PASS_INFO['start_date_local'])
                tweet_text = tweet_text.replace('[SATELLITE]', SATELLITE)
                tweet_text = tweet_text.replace('[CHANNEL A]', PASS_INFO['NOAA Channel A'])
                tweet_text = tweet_text.replace('[CHANNEL B]', PASS_INFO['NOAA Channel B'])
                tweet_text = tweet_text.replace('[MAX ELEVATION]', MAX_ELEVATION)
                tweet_text = tweet_text.replace('[DURATION]', DURATION)

                tweet_text += ' (Click on image to see detail) #weather ' + LOCATION_HASHTAGS

                tweet_image = IMAGE_PATH + FILENAME_BASE + '-' + enhancement + '.jpg'
                try:
                    wxcutils_pi.tweet_text_image(CONFIG_PATH, 'config-twitter.json', tweet_text, tweet_image)
                except:
                    MY_LOGGER.critical('Tweet exception handler: %s %s %s',
                                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                MY_LOGGER.debug('Tweeted!')

                # send to Discord webhooks, if configured
                # can only do this if tweeting as using the tweet's public image URL
                if IMAGE_OPTIONS['discord webhooks'] == 'yes':
                    # sleep to allow Twitter to process the tweet!
                    MY_LOGGER.debug('Sleeping 30 sec to let the Twitter API process')
                    time.sleep(30)
                    MY_LOGGER.debug('Sleep over, try the webhook API')
                    wxcutils_pi.webhooks(CONFIG_PATH, 'config-discord.json', 'config.json',
                                         wxcutils_pi.tweet_get_image_url(CONFIG_PATH, 'config-twitter.json'),
                                         SATELLITE, 'Pass over ' + CONFIG_INFO['Location'], IMAGE_OPTIONS['discord colour'],
                                         MAX_ELEVATION, DURATION, PASS_INFO['start_date_local'],
                                         PASS_INFO['NOAA Channel A'].replace('Channel A: ', ''),
                                         PASS_INFO['NOAA Channel B'].replace('Channel B: ', ''),
                                         pass_description)
                else:
                    MY_LOGGER.debug('Discord webhooks not configured')
    else:
        MY_LOGGER.debug('Tweeting not configured')

    if KEEP_PAGE:
        # migrate files to destinations
        MY_LOGGER.debug('migrate files to destinations')
        migrate_files()
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
