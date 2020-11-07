#!/usr/bin/env python3
"""find files to compare"""


# import libraries
import os
from os import path
import sys
import glob
import csv
from datetime import date, timedelta
import time
import wxcutils


def find_directories(directory):
    """find directories in directory"""
    directory_set = []
    for directories in os.listdir(directory):
        # skip apple mac files
        if directories != '.DS_Store' and directories != '._.DS_Store':
            directory_set.append(directories)
    return directory_set


def iterate_dirctories():
    """iterate through all the dates"""

    for date_dir in DATES:
        if int(date_dir) >= int(start_date_txt) and int(date_dir) <= int(end_date_txt):
            # MY_LOGGER.debug('Parsing %s', date_dir)
            date_dir_val = os.path.join(base_dir, date_dir)
            # iterate through all image directories
            for type_dir in find_directories(date_dir_val):
                # MY_LOGGER.debug('... %s', type_dir)
                file_dir_val = os.path.join(date_dir_val, type_dir)
                # add to type list if not already there
                if type_dir not in TYPES:
                    TYPES.append(type_dir)
                # find all the files
                for file in glob.glob(os.path.join(file_dir_val, '*.*')):
                    # MY_LOGGER.debug('...... %s', file)
                    bits = os.path.split(file)
                    filename, extenstion = os.path.splitext(bits[1])

                    # skip any sanchez images
                    if 'sanchez' not in filename and '.DS_Store' not in filename and '._.DS_Store' not in filename: 
                        # MY_LOGGER.debug('......... %s %s', filename, extenstion)
                        # MY_LOGGER.debug('> %s %s %s %s', date_dir, type_dir, filename, extenstion)
                        if type_dir != 'SCALED' and type_dir != 'CLAHE' and type_dir != 'SANCHEZ' and type_dir != 'LATEST':
                            filename_bits = filename.split('_')
                            file_count = filename_bits[2]
                            if "_IR105_" in filename:
                                file_date = filename_bits[4]
                                file_time = filename_bits[5]
                            else:
                                file_date = filename_bits[3]
                                file_time = filename_bits[4]
                            # MY_LOGGER.debug('>> %s %s %s', file_count, file_date, file_time)
                            FILES.append({'date': date_dir, 'type': type_dir, 'counter': file_count,
                                        'time': file_time, 'filename': filename, "extension": extenstion})
    # show types
    # for type_str in TYPES:
    #     MY_LOGGER.debug('-> %s', type_str)


def find_max_values():
    """find max values"""
    for file_data in FILES:
        # MY_LOGGER.debug('%s %s', file_data['type'], file_data['counter'])
        try:
            if int(file_data['counter']) > int(counter_max[file_data['type']]):
                counter_max[file_data['type']] = int(file_data['counter'])
        except:
            counter_max[file_data['type']] = int(file_data['counter'])
    # show max values
    # for key in counter_max:
    #     MY_LOGGER.debug('%s %d', key, counter_max[key])


def daterange(start_date, end_date):
    """create a date range"""
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def find_missing():
    """find missing images"""
    # iterate through days / types and look for missing files
    # need to go through all days in date range to catch full missing days
    for day in daterange(start_date, end_date):
        day_cmp = day.strftime('%Y%m%d')
        MY_LOGGER.debug('Processing %s', day_cmp)
        for type_str in TYPES:
            if type_str != 'SCALED' and type_str != 'CLAHE' and type_str != 'SANCHEZ' and type_str != 'LATEST':
                counter = 0
                while counter < counter_max[type_str]:
                    counter += 1
                    found = False
                    # see if there is an existing file for this or not
                    for row in FILES:
                        if row['date'] == day_cmp and row['type'] == type_str and int(row['counter']) == counter:
                            # MY_LOGGER.debug('Found %s %s %d', day, type_str, counter)
                            found = True
                            break
                    if not found:
                        # MY_LOGGER.debug('Missing %s %s %d', day, type_str, counter)
                        MISSING.append({'date': day_cmp, 'type': type_str, 'counter': counter})


def save_csv(sc_path, sc_file, sc_ld):
    """save a csv file"""
    keys = sc_ld[0].keys()
    with open(sc_path + sc_file, 'w', newline='')  as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(sc_ld)


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
MODULE = 'synctest'
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
    base_dir = sys.argv[1]
    start_date_txt = sys.argv[2]
    end_date_txt = sys.argv[3]
    station = sys.argv[4]

    MY_LOGGER.debug('start date %d %d %d', int(start_date_txt[0:4]), int(start_date_txt[4:6]), int(start_date_txt[6:]))
    MY_LOGGER.debug('end date %d %d %d', int(end_date_txt[0:4]), int(end_date_txt[4:6]), int(end_date_txt[6:]))

    start_date = date(int(start_date_txt[0:4]), int(start_date_txt[4:6]), int(start_date_txt[6:]))
    end_date = date(int(end_date_txt[0:4]), int(end_date_txt[4:6]), int(end_date_txt[6:])) + timedelta(days=1)

except:
    MY_LOGGER.critical('Exception whilst parsing command line parameters: %s %s %s',
                        sys.argv[1], sys.argv[2], sys.argv[3])
    # re-throw it as this is fatal
    raise

MY_LOGGER.debug('base_dir = %s', base_dir)
MY_LOGGER.debug('date range %s to %s', start_date, end_date)
MY_LOGGER.debug('station = %s', station)

FILES = []
TYPES = []

# find all date directories
MY_LOGGER.debug('Finding date directories')
DATES = find_directories(base_dir)

# iterate through all the dates
MY_LOGGER.debug('Iterate through all files')
iterate_dirctories()

# find the max file counter for an image type
MY_LOGGER.debug('Find max counter per image type')
counter_max = dict()
find_max_values()

MISSING = []
MY_LOGGER.debug('Find missing')
# iterate through days / types and look for missing files
# need to go through all days in date range to catch full missing days
find_missing()

# save out data
MY_LOGGER.debug('Save out results')
wxcutils.save_json(WORKING_PATH, station + '-filefound.json', FILES)
wxcutils.save_json(WORKING_PATH, station + '-filemissing.json', MISSING)
save_csv(WORKING_PATH, station + '-filefound.csv', FILES)
save_csv(WORKING_PATH, station + '-filemissing.csv', MISSING)



MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
