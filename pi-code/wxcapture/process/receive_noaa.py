#!/usr/bin/env python3
"""capture and process NOAA satellite pass
create images plus pass web page"""


# import libraries
import os
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


def scp_files():
    """move files to output directory"""
    # load config
    scp_config = wxcutils.load_json(CONFIG_PATH, 'config-scp.json')
    MY_LOGGER.debug('SCPing files to remote server %s directory %s as user %s',
                    scp_config['remote host'], scp_config['remote directory'],
                    scp_config['remote user'])

    wxcutils.run_cmd('scp ' + OUTPUT_PATH + FILENAME_BASE + '*.html ' +
                     scp_config['remote user'] +
                     '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/')
    wxcutils.run_cmd('scp ' + OUTPUT_PATH + FILENAME_BASE + '*.txt ' +
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
    wxcutils.run_cmd('scp ' + IMAGE_PATH + FILENAME_BASE + '*.jpg ' +
                     scp_config['remote user']
                     + '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/images/')
    wxcutils.run_cmd('scp ' + IMAGE_PATH + FILENAME_BASE + '*.png ' +
                     scp_config['remote user']
                     + '@' + scp_config['remote host'] + ':' +
                     scp_config['remote directory'] + '/images/')
    if CONFIG_INFO['save .wav files'] == 'yes':
        MY_LOGGER.debug('SCPing .wav audio file')
        wxcutils.run_cmd('scp ' + AUDIO_PATH + FILENAME_BASE + '.wav ' +
                         scp_config['remote user']
                         + '@' + scp_config['remote host'] + ':' +
                         scp_config['remote directory'] + '/audio/')
    MY_LOGGER.debug('SCP complete')


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

# extract parameters
SATELLITE_TYPE = sys.argv[1]
SATELLITE_NUM = sys.argv[2]
SATELLITE = SATELLITE_TYPE + ' ' + SATELLITE_NUM
START_EPOCH = sys.argv[3]
DURATION = sys.argv[4]
MAX_ELEVATION = sys.argv[5]
REPROCESS = sys.argv[6]
MY_LOGGER.debug('satellite = %s', SATELLITE)
MY_LOGGER.debug('START_EPOCH = %s', str(START_EPOCH))
MY_LOGGER.debug('duration = %s', str(DURATION))
MY_LOGGER.debug('MAX_ELEVATION = %s', str(MAX_ELEVATION))
MY_LOGGER.debug('REPROCESS = %s', REPROCESS)

# path to output directory
OUTPUT_PATH = HOME + '/wxcapture/output/'

# path to audio directory
AUDIO_PATH = HOME + '/wxcapture/audio/'

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

# to enable REPROCESSing using the original tle file, rename it to match the FILENAME_BASE
wxcutils.copy_file(WORKING_PATH + 'weather.tle', OUTPUT_PATH + FILENAME_BASE + 'weather.tle')

# write out process information
with open(OUTPUT_PATH + FILENAME_BASE + '.txt', 'w') as txt:
    txt.write('./receive_noaa.py ' + sys.argv[1] + ' ' + sys.argv[2] + ' '
              + sys.argv[3] + ' ' + sys.argv[4] + ' ' + sys.argv[5] + ' '
              + sys.argv[6])
txt.close()

# capture pass to wav file
GAIN_COMMAND, GAIN_DESCRIPTION = get_gain()
MY_LOGGER.debug('Frequency = %s', str(PASS_INFO['frequency']))
MY_LOGGER.debug('Gain command = %s', str(GAIN_COMMAND))
MY_LOGGER.debug('Sample rate = %s', IMAGE_OPTIONS['sample rate'])
MY_LOGGER.debug('Duration = %s', DURATION)

# determine the device index based on the serial number
MY_LOGGER.debug('SDR serial number = %s', PASS_INFO['serial number'])
WX_SDR = wxcutils_pi.get_sdr_device(PASS_INFO['serial number'])
MY_LOGGER.debug('SDR device ID = %d', WX_SDR)

if REPROCESS != 'Y':
    wxcutils.run_cmd('timeout ' + DURATION + ' /usr/local/bin/rtl_fm -d ' +
                     str(WX_SDR) + ' -T -f ' + str(PASS_INFO['frequency']) + 'M '
                     + GAIN_COMMAND +
                     ' -s ' + IMAGE_OPTIONS['sample rate'] +
                     ' -E deemp -F 9 - | sox -t raw -e signed -c 1 -b 16 -r '
                     + IMAGE_OPTIONS['sample rate'] + ' - \"' + AUDIO_PATH +
                     FILENAME_BASE + '.wav\" rate 11025')

# create map file
# offset of pass duration / 2 for the pass start time is to avoid
# errors from wxmap which will only create
# the map file if the satellite is in view over the configured
# location at the time specified
# hence the additional time to ensure it is
START_TIME = int(START_EPOCH) + (int(DURATION) * 0.5)
wxcutils.run_cmd('/usr/local/bin/wxmap -T \"' + SATELLITE + '\" -H \"'
                 + WORKING_PATH + 'weather.tle\" -p ' +
                 str(IMAGE_OPTIONS['Population']) + ' -l 0 -o \"' +
                 str(START_TIME) + '\" \"' + IMAGE_PATH + FILENAME_BASE +
                 '-map.png\"')

KEEP_PAGE = True
# build web page for pass
with open(OUTPUT_PATH + FILENAME_BASE + '.html', 'w') as html:
    html.write('<!DOCTYPE html>')
    html.write('<html lang=\"en\"><head>')
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
    html.write('<li>SDR gain - ' + IMAGE_OPTIONS['gain'] + 'dB</li>')
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
            options = ENHANCEMENTS[key]['options'].split()
            optionsLength = len(options)
            if optionsLength == 0:
                cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                             IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                             '-A', '-Q ' + IMAGE_OPTIONS['image quality'],
                             '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                             AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH
                             + FILENAME_BASE + '-' +
                             ENHANCEMENTS[key]['filename'] + '.jpg'],
                            stdout=PIPE, stderr=PIPE)
                MY_LOGGER.debug('optionsLength = 0 %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
            elif optionsLength == 1:
                cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                             IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                             '-A', '-Q ' + IMAGE_OPTIONS['image quality'],
                             '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                             options[0], options[1], AUDIO_PATH +
                             FILENAME_BASE + '.wav', IMAGE_PATH +
                             FILENAME_BASE + '-' +
                             ENHANCEMENTS[key]['filename'] + '.jpg'],
                            stdout=PIPE, stderr=PIPE)
                MY_LOGGER.debug('optionsLength = 1 %s %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
            elif optionsLength == 2:
                cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                             IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                             '-A', '-Q ' + IMAGE_OPTIONS['image quality'],
                             '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                             options[0], options[1], AUDIO_PATH +
                             FILENAME_BASE + '.wav', IMAGE_PATH +
                             FILENAME_BASE + '-' +
                             ENHANCEMENTS[key]['filename'] + '.jpg'],
                            stdout=PIPE, stderr=PIPE)
                MY_LOGGER.debug('optionsLength = 2 %s %s %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
            elif optionsLength == 3:
                cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                             IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                             '-A', '-Q ' + IMAGE_OPTIONS['image quality'],
                             '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                             options[0], options[1], options[2],
                             AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH +
                             FILENAME_BASE + '-' +
                             ENHANCEMENTS[key]['filename'] + '.jpg'],
                            stdout=PIPE, stderr=PIPE)
                MY_LOGGER.debug('optionsLength = 3 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], options[2], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
            elif optionsLength == 4:
                cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                             IMAGE_OPTIONS['Branding'], '-E', '-o', '-I',
                             '-A', '-Q ' + IMAGE_OPTIONS['image quality'],
                             '-m', IMAGE_PATH + FILENAME_BASE + '-map.png',
                             options[0], options[1], options[2], options[3],
                             AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH +
                             FILENAME_BASE + '-' +
                             ENHANCEMENTS[key]['filename'] + '.jpg'],
                            stdout=PIPE, stderr=PIPE)
                MY_LOGGER.debug('optionsLength = 4 %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s ', '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', options[0], options[1], options[2], options[3], AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
            else:
                MY_LOGGER.debug('unhandled options length - need to update code to process this')
                cmd = Popen(['/usr/local/bin/wxtoimg', '-k',
                             IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A',
                             '-Q ' + IMAGE_OPTIONS['image quality'],
                             '-m',
                             IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH +
                             FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE +
                             '-' + ENHANCEMENTS[key]['filename'] + '.jpg'],
                            stdout=PIPE, stderr=PIPE)
                MY_LOGGER.debug('optionsLength = %s %s %s %s %s %s %s %s %s %s %s %s %s', str(optionsLength), '/usr/local/bin/wxtoimg', '-k', IMAGE_OPTIONS['Branding'], '-E', '-o', '-I', '-A', '-Q ' + str(IMAGE_OPTIONS['image quality']), '-m', IMAGE_PATH + FILENAME_BASE + '-map.png', AUDIO_PATH + FILENAME_BASE + '.wav', IMAGE_PATH + FILENAME_BASE + '-' + ENHANCEMENTS[key]['filename'] + '.jpg')
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
                    if IMAGE_OPTIONS['gain'] == 'auto':
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

if IMAGE_OPTIONS['tweet'] == 'yes':
    MY_LOGGER.debug('Tweeting pass - enhancement type = %s', IMAGE_OPTIONS['tweet enhancement'])
    LOCATION_HASHTAGS = '#' + CONFIG_INFO['Location'].replace(', ', ' #').replace(' ', '').replace('#', ' #')
    TWEET_TEXT = 'Latest weather satellite pass over ' + CONFIG_INFO['Location'] +' from ' + SATELLITE + \
        ' on ' + PASS_INFO['start_date_local'] + ' (Click on image to see detail) #weather ' + LOCATION_HASHTAGS

    TWEET_IMAGE = IMAGE_PATH + FILENAME_BASE + '-' + IMAGE_OPTIONS['tweet enhancement'] + '.jpg'
    try:
        wxcutils_pi.tweet_text_image(CONFIG_PATH, 'config-twitter.json', TWEET_TEXT, TWEET_IMAGE)
    except:
        MY_LOGGER.critical('Tweet exception handler: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
    MY_LOGGER.debug('Tweeted!')
else:
    MY_LOGGER.debug('Tweeting not configured')

if KEEP_PAGE:
    # move files to destinations
    MY_LOGGER.debug('using scp')
    scp_files()
else:
    MY_LOGGER.debug('Page not created due to image size')
    MY_LOGGER.debug('Deleting any objects created')
    wxcutils.run_cmd('rm ' + OUTPUT_PATH + FILENAME_BASE + '.html')
    wxcutils.run_cmd('rm ' + IMAGE_PATH + FILENAME_BASE + '*.*')
    wxcutils.run_cmd('rm ' + WORKING_PATH + FILENAME_BASE + '*.*')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
