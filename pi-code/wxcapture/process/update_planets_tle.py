#!/usr/bin/env python3
"""update planets files nightly"""


# import libraries
import os
import sys
from skyfield.api import Loader
import wxcutils


def backup_tle(filename):
    """backup old TLE"""
    # back up the old tle file, only if non-zero size and it exists
    if os.path.isfile(WORKING_PATH + filename):
        if os.path.getsize(WORKING_PATH + filename) != 0:
            MY_LOGGER.debug('backing up %s to %s', WORKING_PATH + filename,
                            WORKING_PATH + filename + '.old')
            wxcutils.move_file(WORKING_PATH, filename,
                               WORKING_PATH, filename + '.old')
        else:
            MY_LOGGER.debug('Current %s is zero length', filename)
            MY_LOGGER.debug('It will not be backed up')
    else:
        MY_LOGGER.debug('Current %s does not exist', filename)
        MY_LOGGER.debug('It can not be backed up')


def validate_tle(filename):
    """validate TLE"""
    # make sure we got a file created, otherwise re-use the old one
    file_exists = True
    file_non_zero_length = True
    if os.path.exists(WORKING_PATH + filename):
        MY_LOGGER.debug('File exists - %s', filename)
        if os.path.getsize(WORKING_PATH + filename) == 0:
            MY_LOGGER.debug('File is empty - %s', filename)
            file_non_zero_length = False
        else:
            MY_LOGGER.debug('File contains data - %s', filename)
    else:
        file_exists = False
        MY_LOGGER.debug('File does not exist - %s', filename)

    if not file_exists or not file_non_zero_length:
        MY_LOGGER.debug('Issue creating / updating %s file', filename)
        MY_LOGGER.debug('re-using old one (if it exists)')
        wxcutils.run_cmd('rm ' + WORKING_PATH + filename)
        wxcutils.move_file(WORKING_PATH, filename + '.old',
                           WORKING_PATH, filename)
    else:
        MY_LOGGER.debug('%s validated successfully', filename)


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
MODULE = 'update_planets_tle'
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
    # backup old tle files
    MY_LOGGER.debug('Backing up old files')
    backup_tle('de421.bsp')

    # update planets info
    MY_LOGGER.debug('Loading new files')
    LOAD = Loader(WORKING_PATH)
    TS = LOAD.timescale()
    PLANETS = LOAD('de421.bsp')

    # validate planets files
    MY_LOGGER.debug('Validating new files')
    validate_tle('de421.bsp')


    MY_LOGGER.debug('Finished')


except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
