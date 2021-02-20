#!/usr/bin/env python3
"""sync EWS-G1 satellite data"""


# import libraries
import os
import sys
import requests
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
MODULE = 'ews-g1'
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


URL_BASE = 'https://satellites.altillimity.com/EWS-G1/'
MY_LOGGER.debug('URL_BASE = %s', URL_BASE)

FILE_BASE = '/home/pi/goes/EWS-G1/'
MY_LOGGER.debug('FILE_BASE = %s', FILE_BASE)

# get the last directory name used for a sync
CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'ews-g1.json')

LAST_DIRECTORY = CONFIG_INFO['Last Directory']
MY_LOGGER.debug('LAST_DIRECTORY = %s', LAST_DIRECTORY)

directories = sorted(listFD(URL_BASE, ''))

last_read = ''

# loop through directories
for directory in directories:
    directory_datetime = directory.split('/')[5]

    # MY_LOGGER.debug('directory_datetime = %s', directory_datetime)

    if directory_datetime >= LAST_DIRECTORY:
        MY_LOGGER.debug('Need to process %s', directory_datetime)
        elements = directory_datetime.split('_')
        date_element = elements[1]
        MY_LOGGER.debug('date_element = %s', date_element)

        image_files = listFD(directory, 'png')

        for file in image_files:
            filename = file.split('/')[-1]
            if 'EWS-G1' in filename:
                MY_LOGGER.debug('filename = %s', filename)
                file_location = FILE_BASE + date_element + '/' + filename[7] + '/'
                MY_LOGGER.debug('file_location = %s', file_location)
                # see if file exists, if not, get it
                if not os.path.exists(file_location + filename):
                    # create directories
                    mk_dir(FILE_BASE + date_element)
                    mk_dir(FILE_BASE + date_element + '/1')
                    mk_dir(FILE_BASE + date_element + '/2')
                    mk_dir(FILE_BASE + date_element + '/3')
                    mk_dir(FILE_BASE + date_element + '/4')
                    mk_dir(FILE_BASE + date_element + '/5')
                    # get file
                    MY_LOGGER.debug('Getting file %s', filename)
                    data = requests.get(file)
                    MY_LOGGER.debug('Writing file %s', filename)
                    open(file_location + filename, 'wb').write(data.content)
                    # non-channel 1 images are ~5k x 5k pixels
                    # channel 1 images are 20832 x 18956 ~190MB each
                    # convert all to jpg images, aligned with GOES images size, which are 5424x5424
                    # keeping  the correct aspect ratio so 5424 x 4936
                    if filename[7] != '1':
                        ratio = ' 1'
                    else:
                        ratio = ' 0.2604'

                    cmd = 'vips resize ' + file_location + filename + ' ' + file_location + filename.replace('.png', '.jpg') + ratio
                    MY_LOGGER.debug('cmd %s', cmd)
                    wxcutils.run_cmd(cmd)
                    # can now delete the original image to save space
                    wxcutils.run_cmd('rm ' + file_location + filename)

                else:
                    MY_LOGGER.debug('File already exists')

        last_read = directory_datetime

# update config file with latest directory
# only if directories were processed
if last_read:
    CONFIG_INFO['Last Directory'] = last_read
    wxcutils.save_json(CONFIG_PATH, 'ews-g1.json', CONFIG_INFO)


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
