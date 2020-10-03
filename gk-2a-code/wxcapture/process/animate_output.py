#!/usr/bin/env python3
"""animate all FD images"""


# import libraries
import os
from os import path
import sys
import glob
import time
import subprocess
import wxcutils




def crawl_images(ci_directory):
    """crawl directory structure for all images
    of the data type directory"""

    for file in glob.glob(os.path.join(ci_directory, '*.*')):
        bits = os.path.split(file)
        l_filename, l_extenstion = os.path.splitext(bits[1])
        sub_bits = l_filename.split('_')
        MY_LOGGER.debug('dir = %s, file = %s, ext = %s, date = %s, time = %s', bits[0], l_filename, l_extenstion, sub_bits[4], sub_bits[5])
        FILES.append({'dir': bits[0], 'file': l_filename, 'ext': l_extenstion, 'datetime': sub_bits[4] + sub_bits[5]})


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def animate(a_frames, a_resolution):
    """create animation file"""
    def add_txt(at_path, at_file, add_duration):
        """add text"""

        if add_duration:
            line = 'file \'' + at_path + '/' + at_file + '\'' + os.linesep + 'duration 0.05' + os.linesep
        else:
            line = 'file \'' + at_path + '/' + at_file + '\'' + os.linesep
        return line

    MY_LOGGER.debug('frames = %d', a_frames)
    a_files = len(FILES)
    a_text = ''

    MY_LOGGER.debug('Going throught the last %d frames', a_frames)
    a_counter = a_files - a_frames
    while  a_counter < a_files:
        a_text = a_text + add_txt(FILES[a_counter]['dir'], FILES[a_counter]['file'] + FILES[a_counter]['ext'], True)
        a_counter +=1
    # add last frame again, but with no duration
    a_text += add_txt(FILES[a_files - 1]['dir'], FILES[a_files - 1]['file'] + FILES[a_files - 1]['ext'], False)

    # save as a file
    wxcutils.save_file(WORKING_PATH, 'framelist.txt', a_text)

    # create animation
    a_res = str(a_resolution) + ':' + str(a_resolution)
    a_res_text = str(a_resolution) + 'x' + str(a_resolution)
    # mobile friendly version
    a_generate = 'ffmpeg -y -threads ' + str(CORES) + ' -stream_loop -1  -i ' + AUDIO + ' -safe 0 -f concat -i ' + WORKING_PATH + 'framelist.txt -shortest -c:v libx264 -pix_fmt yuv420p -vf scale=' + a_res + ' ' + OUTPUT_PATH + PREFIX + '-' + str(a_frames) + '-' + a_res_text + '.mp4'
    MY_LOGGER.debug(a_generate)
    wxcutils.run_cmd(a_generate)
    
    # create file with date time info
    date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    wxcutils.save_file(OUTPUT_PATH, PREFIX + '-' + str(a_frames) + '.txt', date_time)


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'web/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = '/mnt/d/wx/'
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

# base_dir = '/mnt/d/wx/output2/'
base_dir = '/mnt/d/wx/output/'
MY_LOGGER.debug('base_dir = %s', base_dir)

# PREFIX = 'CP'
PREFIX = 'FD'
MY_LOGGER.debug('base_dir = %s', base_dir)


AUDIO = '/mnt/g/weather/GK-2A/audio/bensound-relaxing.mp3'
MY_LOGGER.debug('AUDIO = %s', AUDIO)

CORES = 14
MY_LOGGER.debug('CORES = %s', CORES)

# data store for files list
# currently just for FD
FILES = []

# crawl directories for all files
crawl_images(base_dir)
# sort
FILES = sorted(FILES, key=lambda k: k['datetime'])
num_files = len(FILES)
MY_LOGGER.debug('num_files = %s', num_files)
# save to file system for debugging only
# wxcutils.save_json(WORKING_PATH, 'crawl.json', FILES)
# animate(143 * 3, 2200)
animate(num_files, 2200)


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
