#!/usr/bin/env python3
"""find files to compare"""


# import libraries
import os
import sys
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
    STATION = sys.argv[1]
    BASE_DIR = sys.argv[2]

except:
    MY_LOGGER.critical('Exception whilst parsing command line parameters: %s %s %s',
                       sys.argv[1], sys.argv[2], sys.argv[3])
    # re-throw it as this is fatal
    raise

MY_LOGGER.debug('station = %s', STATION)

# load current master
MASTER = wxcutils.load_json(WORKING_PATH, 'master.json')

# load new set
NEW = wxcutils.load_json(WORKING_PATH, STATION + '-filefound.json')

# find what is in the master but not in the new one
# DELTA = [x for x in MASTER + NEW if x not in MASTER or x not in NEW]
DELTA = [_dict for _dict in NEW if _dict not in MASTER]
NUM_DIFFERENCES = len(DELTA)
MY_LOGGER.debug('Number of differences = %d', NUM_DIFFERENCES)

# save out request from station list
wxcutils.save_json(WORKING_PATH, STATION + '-filerequest.json', DELTA)

if NUM_DIFFERENCES > 0:
    KEYS = DELTA[0].KEYS()
    with open(WORKING_PATH + STATION + '-filerequest.csv', 'w', newline='')  as output_file:
        DICT_WRITER = csv.DictWriter(output_file, KEYS)
        DICT_WRITER.writeheader()
        DICT_WRITER.writerows(DELTA)
else:
    MY_LOGGER.debug('No differences to write to a csv file, writing empty file')
    wxcutils.save_file(WORKING_PATH, STATION + '-filerequest.csv', '')

# create zip command
CMD = 'zip ' + STATION + '-GK-2a.zip '
for line in DELTA:
    CMD += ' ' + BASE_DIR + line['date'] + '/' + line['type'] + '/' + \
        line['filename'] + line['extension']
wxcutils.save_file(WORKING_PATH, STATION + '-zip-command.txt', CMD)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
