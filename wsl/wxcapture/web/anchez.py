#!/usr/bin/env python3
"""speed up sanchez"""


# import libraries
import os
import sys
import subprocess
from subprocess import Popen, PIPE
import wxcutils


def mk_dir(directory):
    """only create if it does not already exist"""
    MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


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


try:
    # extract parameters
    SOURCE_DIR_PARAM = sys.argv[1]
    MY_LOGGER.debug('SOURCE_DIR_PARAM = %s', SOURCE_DIR_PARAM)
    DESTINATION_DIR_PARAM = sys.argv[2]
    MY_LOGGER.debug('DESTINATION_DIR_PARAM = %s', DESTINATION_DIR_PARAM)
    DATE_TIME_PARAM = sys.argv[3]
    MY_LOGGER.debug('DATE_TIME_PARAM = %s', DATE_TIME_PARAM)

except IndexError as exc:
    MY_LOGGER.critical('Exception whilst parsing command line parameters: %s %s %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
    # re-throw it as this is fatal
    raise

date_directory = DATE_TIME_PARAM.split('T')[0]
MY_LOGGER.debug('date_directory = %s', date_directory)

# copy GOES 16 files to the directory
wxcutils.run_cmd('cp -r ' + SOURCE_DIR_PARAM + '/goes16/fd/ch13/*' + date_directory + ' ' + WORKING_PATH)

# copy GOES 17 files to the directory
wxcutils.run_cmd('cp -r ' + SOURCE_DIR_PARAM + '/goes17/fd/ch13/*' + date_directory + ' ' + WORKING_PATH)

# copy GK-2A files to the directory
gk_2a_year = date_directory[0:4]
MY_LOGGER.debug('gk_2a_year = %s', gk_2a_year)
wxcutils.run_cmd('cp ' + SOURCE_DIR_PARAM + 'gk-2a/' + gk_2a_year + '/' + date_directory.replace('-', '') +  '/FD/* ' + WORKING_PATH + date_directory)

# run sanchez
cmd = Popen(['/home/mike/sanchez/Sanchez', 'reproject', '-s', WORKING_PATH + date_directory, '-o', DESTINATION_DIR_PARAM, '-a', '-T', DATE_TIME_PARAM],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            universal_newlines=True)
stdout, stderr = cmd.communicate()
MY_LOGGER.debug('stdout:%s', stdout)
MY_LOGGER.debug('stderr:%s', stderr)

# tidy up working directory
wxcutils.run_cmd('rm ' + WORKING_PATH + date_directory + '/*')
wxcutils.run_cmd('rmdir ' + WORKING_PATH + date_directory)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
