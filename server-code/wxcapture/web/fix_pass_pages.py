#!/usr/bin/env python3
"""move files to web server directory"""


# import libraries
import os
import sys
import wxcutils
import fix_pass_pages_lib


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'fix_pass_pages'
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

# see if args passed
try:
    DIRECTORY = sys.argv[1]
    FILE = sys.argv[2]
except:
    DIRECTORY = ''
    FILE = ''

MY_LOGGER.debug('Starting file fixing')

# find the files to skip, changing only those for satellite passes
if DIRECTORY != '':
    MY_LOGGER.debug('Fixing %s %s', DIRECTORY, FILE)
    fix_pass_pages_lib.fix_file(DIRECTORY + '/', FILE)
else:
    MY_LOGGER.debug('Fixing ALL')
    for filename in fix_pass_pages_lib.find_files(TARGET, '*.html'):
        if 'NOAA' in filename or '.backup' in filename or 'METEOR' in filename \
            or 'SSTV' in filename or 'SAUDISAT' in filename or 'FOX' in filename:
            path_part, file_part = os.path.split(filename)
            MY_LOGGER.debug('Fixing - filename = %s, path = %s, file = %s',
                            filename, path_part, file_part)
            fix_pass_pages_lib.fix_file(path_part + '/', file_part)
        else:
            MY_LOGGER.debug('SKIPing            = %s', filename)


MY_LOGGER.debug('Finished file fixing')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
