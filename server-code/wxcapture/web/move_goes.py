#!/usr/bin/env python3
"""move goes files to web server directory"""


# import libraries
import os
from os import listdir
from os.path import isfile, join
import glob
import sys
import subprocess
import time
import fnmatch
from datetime import datetime, timedelta
from dateutil import rrule
import wxcutils
import fix_pass_pages_lib


def mk_dir(directory):
    """only create if it does not already exist"""
    MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


def find_files(directory, pattern):
    """find files that match the pattern"""
    for root, dirs, files in os.walk(directory):
        MY_LOGGER.debug('find_files %s %s %s', root, dirs, files)
        for base_name in files:
            if fnmatch.fnmatch(base_name, pattern):
                filename = os.path.join(root, base_name)
                yield filename


def build_pass_json():
    """build json file for all passes"""
    MY_LOGGER.debug('building pass json')
    json_data = []
    for filename in find_files(TARGET, '*.html'):
        if filename.split(TARGET)[1][:2] == '20' and 'captures' not in filename and 'meteor' not in filename and 'noaa' not in filename:
            # MY_LOGGER.debug('found pass page - filename = %s', filename)
            bpj_file_path, html_file = os.path.split(filename)
            base_filename, base_extension = os.path.splitext(html_file)
            filename_root = filename[:len(filename) - len(base_extension)]
            # look for all the image files and add to the list
            # to avoid the json file getting too large, extract the enhancement part only
            image_files = glob.glob(bpj_file_path + '/images/' + base_filename + '*.jpg')
            image_enhancements = []
            for entry in image_files:
                if entry[len(entry) - 7:] != '-tn.jpg':
                    result = entry.replace('.jpg', '').replace(bpj_file_path + '/images/', '').replace(base_filename, '')
                    image_enhancements.append(result[1:])

            json_data.append({'path': filename_root.replace(TARGET, ''),
                              'enhancement': image_enhancements
                             })
            # build data for catures pages
            # MY_LOGGER.debug('filename_root = %s', filename_root.replace(TARGET, '')[11:30])
            local_sort = wxcutils.epoch_to_local(wxcutils.utc_to_epoch(filename_root.replace(TARGET, '')[11:30], '%Y-%m-%d-%H-%M-%S'), '%Y-%m-%d-%H-%M-%S')
            # MY_LOGGER.debug('local = %s', local)
            ALL_PASSES.append({'path': filename_root.replace(TARGET, ''),
                               'local sort': local_sort,
                               'local year': local_sort[:4],
                               'local month': local_sort[5:7],
                               'local day': local_sort[8:10],
                               'local time': local_sort[11:19]
                               })
    MY_LOGGER.debug('saving passses.json')
    wxcutils.save_json(TARGET, 'passes.json', json_data)


def move_output_files():
    """move the files from the output directories to the correct locations"""

    find_files(MY_PATH, "*")


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'move_goes'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')

MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# load config
CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

# set up paths
MY_PATH = '/home/mike/wxcapture/goes/'
TARGET = CONFIG_INFO['web doc root location']
CAPTURES_PAGE = 'captures.html'

try:
    # see if args passed
    try:
        REBUILD = sys.argv[1]
    except:
        REBUILD = ''
    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]

    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    MY_LOGGER.debug('Starting file moving')
    FILES_MOVED = move_output_files()
    MY_LOGGER.debug('Finished file moving')

    # if FILES_MOVED or REBUILD == 'rebuild':
    #     MY_LOGGER.debug('Build json passes file')
    #     ALL_PASSES = []
    #     build_pass_json()
    #     MY_LOGGER.debug('Finished json passes file')

    #     MY_LOGGER.debug('Starting capture page building')
    #     build_capture_pages()
    #     MY_LOGGER.debug('Finished capture page building')
    # elif int(time.strftime('%H')) == 1 and int(time.strftime('%M')) in (0, 1) or REBUILD == 'rebuild':
    #     MY_LOGGER.debug('Starting capture page building - overnight run')
    #     build_capture_pages()
    #     MY_LOGGER.debug('Finished capture page building - overnight run')
    # else:
    #     MY_LOGGER.debug('No further work required.')


except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
