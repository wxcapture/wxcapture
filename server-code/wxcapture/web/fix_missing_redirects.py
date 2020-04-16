#!/usr/bin/env python3
"""move files to web server directory"""

import os
import subprocess


import wxcutils


def find_dirs(directory):
    """find files that match the pattern"""
    for root, dirs, files in os.walk(directory):
        if TARGET + '20' in root and 'audio' not in root and 'images' not in root:
            # MY_LOGGER.debug('find_dirs %s', root)
            DAY_DIRS.append(root)


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'fix_missing_redirects'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')

MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# set up paths
MY_PATH = '/home/mike/wxcapture/output/'
TARGET = '/media/storage/html/wxcapture/'
OUTPUT_PATH = '/media/storage/html'

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]

MY_LOGGER.debug('Starting finding missing redirects')

# find all the day level directories
DAY_DIRS = []
find_dirs(TARGET)
for dir_name in DAY_DIRS:
    # MY_LOGGER.debug('directory found = %s', dir_name)
    dir_depth = len(dir_name.replace(TARGET, '').split('/'))
    MY_LOGGER.debug('structure = %s %d', dir_name, dir_depth)

     # always copy to ensure current redirect is there

    # year redirect
    if dir_depth == 1:
        MY_LOGGER.debug('Month redirect page for %s', dir_name)
        test_filename = dir_name + '/index.html'
        MY_LOGGER.debug('Creating index.html page - %s', test_filename)
        wxcutils.copy_file(CONFIG_PATH + 'redirect-1up.html',
                           test_filename)

    # month redirect
    if dir_depth == 2:
        MY_LOGGER.debug('Month redirect page for %s', dir_name)
        test_filename = dir_name + '/index.html'
        MY_LOGGER.debug('Creating index.html page - %s', test_filename)
        wxcutils.copy_file(CONFIG_PATH + 'redirect-0up.html',
                           test_filename)

    # day redirect plus images and audio
    if dir_depth == 3:
        MY_LOGGER.debug('Day redirect page for %s', dir_name)
        test_filename = dir_name + '/index.html'
        MY_LOGGER.debug('Creating index.html page - %s', test_filename)
        wxcutils.copy_file(CONFIG_PATH + 'redirect-1up.html',
                           test_filename)
        test_filename = dir_name + '/audio/index.html'
        MY_LOGGER.debug('Creating index.html page - %s', test_filename)
        wxcutils.copy_file(CONFIG_PATH + 'redirect-2up.html',
                           test_filename)
        test_filename = dir_name + '/images/index.html'
        MY_LOGGER.debug('Creating index.html page - %s', test_filename)
        wxcutils.copy_file(CONFIG_PATH + 'redirect-2up.html',
                           test_filename)


MY_LOGGER.debug('Finished finding missing redirects')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
