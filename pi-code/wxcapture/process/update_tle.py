#!/usr/bin/env python3
"""update weather.tle file hourly"""


# import libraries
import os
import sys
from urllib.request import urlopen
import wxcutils


def backup_tle():
    """backup old TLE"""
    MY_LOGGER.debug('backup old TLE')
    # back up the old tle file, only if non-zero size and it exists
    if os.path.isfile(WORKING_PATH + TLE_FILENAME):
        if os.path.getsize(WORKING_PATH + TLE_FILENAME) != 0:
            wxcutils.move_file(WORKING_PATH, TLE_FILENAME,
                               WORKING_PATH, TLE_FILENAME + '.old')
        else:
            MY_LOGGER.debug('Current %s is zero length', TLE_FILENAME)
            MY_LOGGER.debug('It will not be backed up')
    else:
        MY_LOGGER.debug('Current %s does not exist', TLE_FILENAME)
        MY_LOGGER.debug('It can not be backed up')


def refresh_tle(filename):
    """refresh TLE"""
    MY_LOGGER.debug('refresh TLE - %s', filename)

    # get list of sats we are interested in
    sats = []
    MY_LOGGER.debug('Finding satellites we need to process')
    for key, value in SATELLITE_INFO.items():
        MY_LOGGER.debug('key = %s, value = %s', key, value)
        for line in SATELLITE_INFO[key]:
            # MY_LOGGER.debug('name = %s', line['name'])
            sats.append(line['name'])
    MY_LOGGER.debug('sats = %s', sats)

    MY_LOGGER.debug('getting %s.txt from celestrak', filename)
    with urlopen('https://www.celestrak.com/NORAD/elements/' +
                    filename + '.txt') as file_in:
        while True:
            read_data1 = file_in.readline().decode('utf-8')
            read_data2 = file_in.readline().decode('utf-8')
            read_data3 = file_in.readline().decode('utf-8')
            if read_data1:
                if read_data1.rstrip() in sats:
                    MY_LOGGER.debug('>>%s<<', read_data1.rstrip())
                    TLE_INFO.append({"line_1":read_data1,
                                     "line_2":read_data2,
                                     "line_3":read_data3})
            else:
                break

    MY_LOGGER.debug('New tle file = %s', TLE_INFO)


def write_file():
    """write TLE"""
    # update TLE
    MY_LOGGER.debug('write new TLE to %s', WORKING_PATH + TLE_FILENAME)
    file_out = open(WORKING_PATH + TLE_FILENAME, 'w+')
    for satellite in TLE_INFO:
        MY_LOGGER.debug('%s %s %s', satellite['line_1'], satellite['line_2'], satellite['line_3'])
        file_out.write(satellite['line_1'])
        file_out.write(satellite['line_2'])
        file_out.write(satellite['line_3'])
    file_out.close()

    # make sure we got a file created, otherwise re-use the old one
    if os.path.getsize(WORKING_PATH + TLE_FILENAME) == 0:
        MY_LOGGER.debug('Issue updating %s file resulting in zero length file', TLE_FILENAME)
        MY_LOGGER.debug('re-using old one')
        wxcutils.run_cmd('rm ' + WORKING_PATH + TLE_FILENAME)
        wxcutils.move_file(WORKING_PATH, TLE_FILENAME + '.old', WORKING_PATH, TLE_FILENAME)
    else:
        MY_LOGGER.debug('weather.tle created with non-zero size')


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
MODULE = 'update_tle'
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
    # filenames
    TLE_FILENAME = 'weather.tle'

    # load satellites
    SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'satellites.json')

    # backup old tle file
    backup_tle()

    # refresh TLE file
    TLE_INFO = []
    # refresh_tle('weather')
    # refresh_tle('stations')
    # refresh_tle('amateur')
    refresh_tle('active')

    # write out TLE file
    write_file()

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
