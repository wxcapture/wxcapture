#!/usr/bin/env python3
"""sync web satellite data"""


# import libraries
from genericpath import exists
import os
import sys
import time
import datetime
import requests
import subprocess
from bs4 import BeautifulSoup
import wxcutils


def listFD(url, ext=''):
    page = requests.get(url).text
    # print(page)
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]


def mk_dir(directory):
    """only create if it does not already exist"""
    # MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %Y %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %Y %H:%M')


def get_last_generated_text(lgt_filename):
    """build the last generated text"""
    last_generated_text = 'Last generated at ' + get_local_date_time() + ' ' + \
                            LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    MY_LOGGER.debug('last_generated_text = %s - for file %s', last_generated_text, lgt_filename)
    return last_generated_text


def proccess_satellite(sat_info):
    """process satellite info from web"""

    # set up variables
    file_directory = FILE_BASE + sat_info['File base']
    MY_LOGGER.debug('file_directory = %s', file_directory)
    MY_LOGGER.debug('last directory = %s', sat_info['Last Directory'])
    MY_LOGGER.debug('URL = %s', sat_info['URL'])
    
    directories = sorted(listFD(sat_info['URL'], ''))

    # loop through directories
    for directory in directories:
        # MY_LOGGER.debug('directory = %s', directory)
        directory_datetime = directory.split('/')[5]

        # MY_LOGGER.debug('directory_datetime = %s', directory_datetime)

        if directory_datetime >= sat_info['Last Directory']:
            MY_LOGGER.debug('-' * 5)
            MY_LOGGER.debug('Need to process %s', directory_datetime)
            elements = directory_datetime.split('_')
            date_element = elements[0]
            MY_LOGGER.debug('date_element = %s', date_element)

            image_files = listFD(directory, 'png')
            channel_locator = len(sat_info['File in prefix']) + 1
            MY_LOGGER.debug('channel_locator = %s', channel_locator)

            # create directories
            mk_dir(file_directory + '/' +  date_element)
            mk_dir(file_directory + '/' +  date_element + '/1')
            mk_dir(file_directory + '/' +  date_element + '/2')
            mk_dir(file_directory + '/' +  date_element + '/3')
            mk_dir(file_directory + '/' +  date_element + '/4')
            mk_dir(file_directory + '/' +  date_element + '/5')
            mk_dir(file_directory + '/' +  date_element + '/FC')

            existsCount = 0

            for file in image_files:
                filename = file.split('/')[-1]
                if sat_info['File in prefix'] in filename:
                    MY_LOGGER.debug('filename = %s', filename)
                    channel = '?'
                    if filename[channel_locator] == 'F':
                        file_location = file_directory + '/' + date_element + '/FC/'
                        channel = 'FC'
                    else:
                        file_location = file_directory + '/' + date_element + '/' + filename[channel_locator] + '/'
                        channel = filename[channel_locator]

                    MY_LOGGER.debug('file_location = %s', file_location)
                    MY_LOGGER.debug('channel = %s', channel)

                    # see if file exists, if not, get it
                    if not os.path.exists(file_location + filename.replace('.png', '.jpg')):
                        # get file
                        MY_LOGGER.debug('Getting file %s', filename)

                        data = requests.get(file)
                        MY_LOGGER.debug('Writing file %s', filename)
                        open(file_location + filename, 'wb').write(data.content)
                        # non-channel 1 and FC images are ~5k x 5k pixels
                        # channel 1 and FC images are 20832 x 18956 ~190MB each
                        # convert all to jpg images, aligned with GOES images size, which are 5424x5424
                        # keeping  the correct aspect ratio so 5424 x 4936
                        if channel not in ('1', 'FC'):
                            ratio = ' 1'
                        else:
                            ratio = ' 0.2604'

                        cmd = 'vips resize ' + file_location + filename + ' ' + file_location + filename.replace('.png', '.jpg') + ratio
                        MY_LOGGER.debug('cmd %s', cmd)
                        wxcutils.run_cmd(cmd)

                        # can now delete the original image to save space
                        wxcutils.run_cmd('rm ' + file_location + filename)

                        # copy file to output folder
                        wxcutils.copy_file(file_location + filename.replace('.png', '.jpg'), OUTPUT_PATH + sat_info['File out prefix'] + '-' + channel + '.jpg')

                        # create thumbnail and txt file
                        cmd = 'vips resize ' + file_location + filename.replace('.png', '.jpg') + ' ' + OUTPUT_PATH + sat_info['File out prefix'] + '-' + channel + '-tn.jpg' + ' 0.1'
                        MY_LOGGER.debug('cmd %s', cmd)
                        wxcutils.run_cmd(cmd)
                        
                        # create file with date time info
                        MY_LOGGER.debug('Writing out last generated date file')
                        wxcutils.save_file(OUTPUT_PATH, sat_info['File out prefix'] + '-' + channel + '.txt', get_last_generated_text(filename.replace('.png', '.jpg')))

                    else:
                        MY_LOGGER.debug('Already exists %s', file_location + filename)
                        existsCount += 1

                # check age of directory to skip over "OLD" directories
                # 2021-08-11_16-56
                directory_datetime_dt = datetime.datetime.strptime(directory_datetime, '%Y-%m-%d_%H-%M')
                directory_datetime_epoch = wxcutils.utc_datetime_to_epoch(directory_datetime_dt)
                current_epoch = time.time()
                directory_age= current_epoch - float(directory_datetime_epoch)
                MY_LOGGER.debug('current_epoch = %f', current_epoch)
                MY_LOGGER.debug('directory_datetime_epoch = %f', float(directory_datetime_epoch))
                MY_LOGGER.debug('age = %f', directory_age)


                if existsCount == 6 or directory_age > (6 * 60 * 60):
                    if existsCount == 6:
                        MY_LOGGER.debug('all 6 files exist - update last directory')
                    else:
                        MY_LOGGER.debug('Directory age is too old, assuming files will not appear - 6 hours')
                    if directory_datetime > sat_info['Last Directory']:
                        MY_LOGGER.debug('Old last directory = %s, new last directory = %s', sat_info['Last Directory'], directory_datetime)
                        sat_info['Last Directory'] = directory_datetime
                    else:
                        MY_LOGGER.debug('No change required - Old last directory = %s, new last directory = %s', sat_info['Last Directory'], directory_datetime)




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
MODULE = 'web'
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

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]
MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

FILE_BASE = '/home/pi/goes/'
MY_LOGGER.debug('FILE_BASE = %s', FILE_BASE)

# get the last directory name used for a sync
SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'web.json')

# loop through active satellites
for key, value in SATELLITE_INFO.items():
        for si in SATELLITE_INFO[key]:
            if si['Active'] == 'yes':
                MY_LOGGER.debug('-' * 20)
                MY_LOGGER.debug(si)
                try:
                    proccess_satellite(si)
                except:
                    MY_LOGGER.debug('Exception whilst processing satellite %s', si['Name'])
                    MY_LOGGER.error('Loop exception handler: %s %s %s',
                                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

# save updated config
wxcutils.save_json(CONFIG_PATH, 'web.json', SATELLITE_INFO)


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
