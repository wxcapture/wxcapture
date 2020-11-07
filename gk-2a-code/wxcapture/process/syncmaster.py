#!/usr/bin/env python3
"""find files to compare"""


# import libraries
import os
from os import path
import sys
import glob
from datetime import date, timedelta
import time
import csv
import wxcutils


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
MODULE = 'syncmaster'
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
    station = sys.argv[1]
    base_dir = sys.argv[2]

except:
    MY_LOGGER.critical('Exception whilst parsing command line parameters: %s %s %s',
                        sys.argv[1], sys.argv[2], sys.argv[3])
    # re-throw it as this is fatal
    raise

MY_LOGGER.debug('station = %s', station)

# load current master
MASTER = wxcutils.load_json(WORKING_PATH, 'master.json')

# load new set
NEW = wxcutils.load_json(WORKING_PATH, station + '-filefound.json')

# find what is in the master but not in the new one
# DELTA = [x for x in MASTER + NEW if x not in MASTER or x not in NEW]
DELTA = [_dict for _dict in NEW if _dict not in MASTER]
num_differences = len(DELTA)
MY_LOGGER.debug('Number of differences = %d', num_differences)

# save out request from station list
wxcutils.save_json(WORKING_PATH, station + '-filerequest.json', DELTA)

if num_differences >0:
    keys = DELTA[0].keys()
    with open(WORKING_PATH + station + '-filerequest.csv', 'w', newline='')  as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(DELTA)
else:
    MY_LOGGER.debug('No differences to write to a csv file, writing empty file')
    wxcutils.save_file(WORKING_PATH, station + '-filerequest.csv', '')

# create zip command
cmd = 'zip ' + station + '-GK-2a.zip '
for line in DELTA:
    cmd += ' ' + base_dir + line['date'] + '/' + line['type'] + '/' + line['filename'] + line['extension']
wxcutils.save_file(WORKING_PATH, station + '-zip-command.txt', cmd)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
