#!/usr/bin/env python3
"""capture and process ISS satellite pass
create images plus pass web page"""

# capture and process ISS satellite pass
# create audio plus pass web page

# import libraries
import os
import time
import sys
import subprocess
from subprocess import Popen, PIPE
import wxcutils
import wxcutils_pi


def get_gain():
    """determine the gain setting, either auto or defined"""
    command = ''
    description = ''
    if IMAGE_OPTIONS['gain'] == 'auto':
        description = 'Automatic gain control'
    else:
        command = ' -g ' + IMAGE_OPTIONS['gain']
        description = 'Gain set to ' + IMAGE_OPTIONS['gain']
    MY_LOGGER.debug('gain command = %s', command)
    MY_LOGGER.debug('description = %s', description)
    return command, description


def get_bias_t():
    """determine if we turn on the bias t"""
    command = ''
    if PASS_INFO['bias t'] == 'on':
        command = ' -T '
    MY_LOGGER.debug('bias t command = %s', command)
    return command


def scp_files():
    """move files to output directory"""
    # load config
    scp_config = wxcutils.load_json(CONFIG_PATH, 'config-scp.json')
    MY_LOGGER.debug('SCPing files to remote server %s directory %s as user %s',
                    scp_config['remote host'], scp_config['remote directory'],
                    scp_config['remote user'])

    wxcutils.run_cmd('scp ' + OUTPUT_PATH + FILENAME_BASE + '.html ' +
                     scp_config['remote user'] +
                     '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/')
    wxcutils.run_cmd('scp ' + OUTPUT_PATH + FILENAME_BASE + '.txt ' +
                     scp_config['remote user']
                     + '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/')
    wxcutils.run_cmd('scp ' + OUTPUT_PATH + FILENAME_BASE +'.json ' +
                     scp_config['remote user']
                     + '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/')
    wxcutils.run_cmd('scp ' + OUTPUT_PATH + FILENAME_BASE + 'weather.tle ' +
                     scp_config['remote user'] + '@' +
                     scp_config['remote host']
                     + ':' + scp_config['remote directory'] + '/')
    MY_LOGGER.debug('SCPing .png image file')
    wxcutils.run_cmd('scp ' + IMAGE_PATH + FILENAME_BASE + '*.png ' +
                     scp_config['remote user']
                     + '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/images/')
    MY_LOGGER.debug('SCPing .wav audio file')
    wxcutils.run_cmd('scp ' + AUDIO_PATH + FILENAME_BASE + '.wav ' +
                     scp_config['remote user']
                     + '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/audio/')
    MY_LOGGER.debug('SCP complete')


def find_files():
    """find any image files created"""
    counter = 0
    for file in os.listdir(WORKING_PATH):
        if file.endswith('.png'):
            MY_LOGGER.debug('Found file %s', file)
            counter += 1
            # rename file to include the FILENAME_BASE
            # and to move to the IMAGE_PATH directory
            wxcutils.move_file(WORKING_PATH, file,
                               IMAGE_PATH, FILENAME_BASE +  '-sstv-' + str(counter) + '.png')
            IMAGE_FILES.append(FILENAME_BASE + '-sstv-' + str(counter) + '.png')
    MY_LOGGER.debug('Found %d files', counter)
    MY_LOGGER.debug(IMAGE_FILES)
    return counter

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
MODULE = 'receive_iss'
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
        SATELLITE = sys.argv[1]
        START_EPOCH = sys.argv[2]
        DURATION = sys.argv[3]
        MAX_ELEVATION = sys.argv[4]
        REPROCESS = sys.argv[5]
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
    IMAGE_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-ISS.json')

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-2]

    # create filename base
    FILENAME_BASE = wxcutils.epoch_to_utc(START_EPOCH, '%Y-%m-%d-%H-%M-%S') + \
        '-' + SATELLITE.replace(' ', '_').replace('(', '').replace(')', '')
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
        txt.write('./receive-ISS.py ' + sys.argv[1] + ' ' + sys.argv[2] +
                  ' ' + sys.argv[3] + ' ' + sys.argv[4] + ' ' + sys.argv[5] +
                  ' ' + sys.argv[6])
    txt.close()

    # determine the device index based on the serial number
    MY_LOGGER.debug('SDR serial number = %s', PASS_INFO['serial number'])
    WX_SDR = wxcutils_pi.get_sdr_device(PASS_INFO['serial number'])
    MY_LOGGER.debug('SDR device ID = %d', WX_SDR)

    # capture pass to wav file
    if REPROCESS != 'Y':
        GAIN_COMMAND, GAIN_DESCRIPTION = get_gain()
        BIAS_T = get_bias_t()

        # Sleep until the required start time
        # to account for at scheduler starting up to 59 seconds early
        wxcutils_pi.sleep_until_start(float(START_EPOCH))

        wxcutils.run_cmd('timeout ' + DURATION + ' /usr/local/bin/rtl_fm -d ' +
                         str(WX_SDR) + BIAS_T + ' -M fm -f ' + str(PASS_INFO['frequency']) +
                         'M -s 48k ' + GAIN_COMMAND +
                         ' -p 0 | sox -t raw -r 48k -c 1 -b 16 -e s - -t wav \"' +
                         AUDIO_PATH + FILENAME_BASE + '.wav\" rate 48k')
    MY_LOGGER.debug('-' * 30)

    # need to ensure that the following are running:
    # * pactl load-module module-null-sink sink_name=virtual-cable
    # * qsstv

    # start the playback
    MY_LOGGER.debug('start pactl to play back the recording to QSSTV')
    # paplay -d virtual-cable /home/pi/sstv/audio/2019-08-02-14-16-25-ISS_ZARYA.wav
    CMD = Popen(['/usr/bin/paplay', '-d', 'virtual-cable',
                 AUDIO_PATH + FILENAME_BASE + '.wav'], stdout=PIPE, stderr=PIPE)
    STDOUT, STDERR = CMD.communicate()
    MY_LOGGER.debug('stdout:%s', STDOUT)
    MY_LOGGER.debug('stderr:%s', STDERR)

    # with .communicate, will wait for playback to continue
    # sleep 30 seconds to enable any final processing to complete
    MY_LOGGER.debug('sleep 30 seconds for final processing')
    time.sleep(30)
    MY_LOGGER.debug('sleep completed')

    # find any images created
    IMAGE_FILES = []
    IMAGE_COUNT = find_files()

    MY_LOGGER.debug('-' * 30)

    # build web page for pass
    with open(OUTPUT_PATH + FILENAME_BASE + '.html', 'w') as html:
        html.write('<!DOCTYPE html>')
        html.write('<html lang=\"en\"><head>')
        html.write('<meta charset=\"UTF-8\">'
                   '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                   '<meta name=\"description\" content=\"Satellite pass capture page for NOAA / Meteor / International Space Station (ISS) SSTV / Amsat (Amateur Satellites)\">'
                   '<meta name=\"keywords\" content=\"wxcapture, weather, satellite, NOAA, Meteor, images, ISS, Zarya, SSTV, Amsat, orbit, APT, LRPT, SDR, Mike, KiwiinNZ, Albert, Technobird22, Predictions, Auckland, New Zealand, storm, cyclone, hurricane, front, rain, wind, cloud\">'
                   '<meta name=\"author\" content=\"WxCapture\">')
        html.write('<title>Satellite Pass Audio</title></head>')
        html.write('<body><h2>' + SATELLITE + '</h2>')
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
        html.write('<li>SDR type - ' + PASS_INFO['sdr type'] +
                   ' (' + PASS_INFO['chipset'] + ')</li>')
        html.write('<li>SDR gain - ' + IMAGE_OPTIONS['gain'] + 'dB</li>')
        html.write('<li>Antenna - ' + PASS_INFO['antenna'] + ' (' +
                   PASS_INFO['centre frequency'] + ')</li>')
        html.write('<li>Frequency range - ' + PASS_INFO['frequency range'] + '</li>')
        html.write('<li>Modules - ' + PASS_INFO['modules'] + '</li>')
        html.write('</ul>')
        html.write('<img src=\"images/' + FILENAME_BASE + '-plot.png\">')
        html.write('<h2>Decoded Images</h2>')

        if IMAGE_COUNT == 0:
            html.write('<p>No images could be automatically decoded.</p>')
        else:
            html.write('<table>')
            for row in IMAGE_FILES:
                html.write('<tr><td>')
                html.write('<img src=\"images/' + row + '\">')
                html.write('</td></tr>')
            html.write('</table>')

        html.write('<a href=\"audio/' + FILENAME_BASE +
                   '.wav' + '\"><h2>ISS Audio</h2></a>')

        html.write('<p>Click on the link to play or download the audio .wav file.</p>')


        html.write('</body></html>')

    html.close()

    # move files to destinations
    MY_LOGGER.debug('using scp')
    scp_files()
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
