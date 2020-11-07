#!/usr/bin/env python3
"""find files to migrate"""


# import libraries
import os
from os import path
import sys
import glob
import time
import subprocess
import wxcutils


def find_directories(directory):
    """find directories in directory"""
    directory_set = []
    for directories in os.listdir(directory): 
        directory_set.append(directories)
    return directory_set


def find_latest_directory(directory):
    """find latest directory in directory"""
    latest = 0
    latest_dir = ''
    for directories in os.listdir(directory):
        directories_num = int(directories.replace('-',''))
        if directories_num > latest:
            latest = directories_num
            latest_dir = directories
    return str(latest_dir)


def find_latest_file(directory):
    """find latest file in directory based on last modified timestamp"""
    latest_timestamp = 0.0
    latest_filename = ''
    for filename in os.listdir(directory):
        file_timestamp = os.path.getmtime(os.path.join(directory, filename))
        if file_timestamp > latest_timestamp:
            latest_filename = filename
            latest_timestamp = file_timestamp
    MY_LOGGER.debug('latest_filename = %s, latest_timestamp = %f', latest_filename, latest_timestamp)
    return latest_filename


def find_latest_file_contains(directory, contains):
    """find latest file matching a pattern in directory based on last modified timestamp"""
    latest_timestamp = 0.0
    latest_filename = ''
    for filename in os.listdir(directory):
        if contains in filename:
            file_timestamp = os.path.getmtime(os.path.join(directory, filename))
            if file_timestamp > latest_timestamp:
                latest_filename = filename
                latest_timestamp = file_timestamp
    MY_LOGGER.debug('latest_filename = %s, latest_timestamp = %f', latest_filename, latest_timestamp)
    return latest_filename


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def create_thumbnail(ct_directory, ct_extension):
    """create thumbnail of the image"""
    wxcutils.run_cmd('convert \"' + OUTPUT_PATH + ct_directory + ct_extension + 
                        '\" -resize 9999x500 ' + OUTPUT_PATH + ct_directory + '-tn' + ct_extension)


def process_goes(sat_num):
    """process GOES xx files"""

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = base_dir + 'goes' + sat_num
    MY_LOGGER.debug('GOES%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    type_directories = find_directories(sat_dir)
    for type_directory in type_directories:
        MY_LOGGER.debug('--')
        MY_LOGGER.debug('type_directory = %s', type_directory)
        channels_directory = os.path.join(sat_dir, type_directory)
        MY_LOGGER.debug('channels_directory = %s', channels_directory)
        channels_directories = find_directories(channels_directory)
        for channel_directory in channels_directories:
            MY_LOGGER.debug('---')
            MY_LOGGER.debug('channel_directory = %s', channel_directory)
            search_directory = os.path.join(channels_directory, channel_directory)
            latest_directory = find_latest_directory(search_directory)
            MY_LOGGER.debug('latest_directory = %s', latest_directory)

            # find the latest file
            latest_dir = os.path.join(search_directory, latest_directory)
            latest_file = find_latest_file(latest_dir)
            MY_LOGGER.debug('latest_file = %s', latest_file)
            filename, extenstion = os.path.splitext(latest_file) 
            new_filename = 'goes_' + sat_num + '_' + type_directory + '_' + channel_directory

            # see when last saved
            stored_timestamp = 0.0
            try:
                stored_timestamp = latest_timestamps[new_filename + extenstion]
            except NameError:
                pass
            except KeyError:
                pass

            # date time for original file
            latest = os.path.getmtime(os.path.join(latest_dir, latest_file))

            MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

            if stored_timestamp != int(latest):
                # new file found which hasn't yet been copied over

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(os.path.join(latest_dir, latest_file), os.path.join(OUTPUT_PATH, new_filename + extenstion))

                # create thumbnail
                create_thumbnail(new_filename, extenstion)

                 # create file with date time info
                date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
                wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', date_time)

                # update latest
                latest_timestamps[new_filename + extenstion] = int(latest)
    
    MY_LOGGER.debug('---------------------------------------------')


def process_himawari(sat_num):
    """process Himawari xx files"""

    # Note that this code only looks in the latest directory only
    # It is possible that there is a later image of a type only in
    # a previous day's file, but this will be missed with the
    # current search approach

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = base_dir + 'himawari' + sat_num
    MY_LOGGER.debug('Himawari%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    image_types = ['IR', 'VS', 'WV']

    # find directories
    type_directories = find_directories(sat_dir)
    for type_directory in type_directories:
        MY_LOGGER.debug('--')
        MY_LOGGER.debug('type_directory = %s', type_directory)
        channels_directory = os.path.join(sat_dir, type_directory)

        latest_directory = find_latest_directory(channels_directory)
        MY_LOGGER.debug('latest_directory = %s', latest_directory)
        latest_dir = os.path.join(os.path.join(sat_dir, type_directory), latest_directory)
        MY_LOGGER.debug('latest_dir = %s', latest_dir)

        for image_type in image_types:
            MY_LOGGER.debug('image_type = %s', image_type)
            latest_file = find_latest_file_contains(latest_dir, image_type)
            MY_LOGGER.debug('latest_file = %s', latest_file)

            filename, extenstion = os.path.splitext(latest_file) 
            new_filename = 'himawari_' + sat_num + '_' + type_directory + '_' + image_type

            # see when last saved
            stored_timestamp = 0.0
            try:
                stored_timestamp = latest_timestamps[new_filename + extenstion]
            except NameError:
                pass
            except KeyError:
                pass

            # date time for original file
            latest = os.path.getmtime(os.path.join(latest_dir, latest_file))

            MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

            if stored_timestamp != int(latest):
                # new file found which hasn't yet been copied over

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(os.path.join(latest_dir, latest_file), os.path.join(OUTPUT_PATH, new_filename + extenstion))

                # create thumbnail
                create_thumbnail(new_filename, extenstion)

                 # create file with date time info
                date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
                wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', date_time)

                # update latest
                latest_timestamps[new_filename + extenstion] = int(latest)

    MY_LOGGER.debug('---------------------------------------------')

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
MODULE = 'find_files'
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


# try:
# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]

base_dir = '/home/pi/goes/'
MY_LOGGER.debug('base_dir = %s', base_dir)

# load latest times data
latest_timestamps = wxcutils.load_json(OUTPUT_PATH, 'goes_info.json')

# process GOES 17 files
process_goes('17')

# process GOES 16 files
process_goes('16')

# process Himawari 8 files
process_himawari('8')


# save latest times data
wxcutils.save_json(OUTPUT_PATH, 'goes_info.json', latest_timestamps)

# rsync files to server
wxcutils.run_cmd('rsync -rt ' + OUTPUT_PATH + ' mike@192.168.100.18:/home/mike/wxcapture/goes')

# except:
#     MY_LOGGER.critical('Global exception handler: %s %s %s',
#                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
