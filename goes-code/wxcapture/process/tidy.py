#!/usr/bin/env python3
"""find files to delete """


# import libraries
import os
import time
import glob
import subprocess
import wxcutils


def find_directories(directory):
    """find directories in directory"""
    directory_set = []
    for directories in os.listdir(directory):
        directory_set.append(directories)
    return directory_set


def process_goes(sat_num):
    """process GOES xx files"""

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'goes' + sat_num
    MY_LOGGER.debug('GOES%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories

    type_directories = find_directories(sat_dir)

    for type_directory in type_directories:
        # MY_LOGGER.debug('--')
        # MY_LOGGER.debug('type_directory = %s', type_directory)
        type_path = sat_dir  + '/' + type_directory
        view_directories = find_directories(type_path)

        for view_directory in view_directories:
            # MY_LOGGER.debug('--')
            # MY_LOGGER.debug('view_directory = %s', view_directory)
            view_path = type_path  + '/' + view_directory
            view_directories = find_directories(view_path)

            for date_directory in find_directories(view_path):
                # MY_LOGGER.debug('--')
                # MY_LOGGER.debug('date_directory = %s', date_directory)
                date_path = view_path  + '/' + date_directory
                view_directories = find_directories(date_path)

                for filename in os.listdir(date_path):
                    # date time for the file
                    file_age = TIME_NOW - os.path.getmtime(os.path.join(date_path, filename))
                    if file_age > MIN_AGE:
                        MY_LOGGER.debug('DELETE - %s %f %f %f', date_path + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                        wxcutils.run_cmd('rm ' + date_path + '/' + filename)
                    # else:
                    #     MY_LOGGER.debug('keep   - %s %f %f %f', date_path + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

                # directory may be empty, if so, remove it
                if not os.listdir(date_path):
                    MY_LOGGER.debug('deleting empty directory - %s', date_path)
                    wxcutils.run_cmd('rmdir ' + date_path)

    MY_LOGGER.debug('---------------------------------------------')


def process_himawari(sat_num):
    """process Himawari xx files"""

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'himawari' + sat_num
    MY_LOGGER.debug('Himawari%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    type_directories = find_directories(sat_dir)
    for type_directory in type_directories:
        # MY_LOGGER.debug('--')
        # MY_LOGGER.debug('type_directory = %s', type_directory)
        channels_directory = os.path.join(sat_dir, type_directory)

        for date_directory in find_directories(channels_directory):
            # MY_LOGGER.debug('date_directory = %s', date_directory)

            for filename in os.listdir(channels_directory + '/' + date_directory):
                # date time for the file
                file_age = TIME_NOW - os.path.getmtime(os.path.join(channels_directory + '/' + date_directory, filename))
                if file_age > MIN_AGE:
                    MY_LOGGER.debug('DELETE - %s %f %f %f', channels_directory + '/' + date_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                    wxcutils.run_cmd('rm ' + channels_directory + '/' + date_directory + '/' + filename)
                # else:
                #     MY_LOGGER.debug('keep   - %s %f %f %f', channels_directory + '/' + date_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

            # directory may be empty, if so, remove it
            if not os.listdir(channels_directory + '/' + date_directory):
                MY_LOGGER.debug('deleting empty directory - %s', channels_directory + '/' + date_directory)
                wxcutils.run_cmd('rmdir ' + channels_directory + '/' + date_directory)

    MY_LOGGER.debug('---------------------------------------------')


def process_nws():
    """process nws files"""

    # note that this code is a work around for an issue with goestools
    # https://github.com/pietern/goestools/issues/100
    # GOES nws directory / filenames are incorrect #100
    # once fixed, this code will need to be updated

    MY_LOGGER.debug('---------------------------------------------')
    MY_LOGGER.debug('NWS')

    fixed_dir = BASEDIR + 'nwsdata/'
    MY_LOGGER.debug('fixed_dir = %s', fixed_dir)

    for date_directory in find_directories(fixed_dir):
        # MY_LOGGER.debug('date_directory = %s', date_directory)

        for filename in os.listdir(fixed_dir + '/' + date_directory):
            # date time for the file
            file_age = TIME_NOW - os.path.getmtime(os.path.join(fixed_dir + '/' + date_directory, filename))
            if file_age > MIN_AGE:
                MY_LOGGER.debug('DELETE - %s %f %f %f', fixed_dir + '/' + date_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                wxcutils.run_cmd('rm ' + fixed_dir + '/' + date_directory + '/' + filename)
            # else:
            #     MY_LOGGER.debug('keep   - %s %f %f %f', fixed_dir + '/' + date_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

        # directory may be empty, if so, remove it
        if not os.listdir(fixed_dir + '/' + date_directory):
            MY_LOGGER.debug('deleting empty directory - %s', fixed_dir + '/' + date_directory)
            wxcutils.run_cmd('rmdir ' + fixed_dir + '/' + date_directory)

    MY_LOGGER.debug('---------------------------------------------')


def process_gk_2a():
    """process GK-2A files"""
    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'gk-2a'
    MY_LOGGER.debug('GK-2A')
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    for date_directory in find_directories(sat_dir):
        MY_LOGGER.debug('date_directory = %s', date_directory)
        dates_directory = os.path.join(sat_dir, date_directory)

        type_directories = find_directories(dates_directory)
        for type_directory in type_directories:
            MY_LOGGER.debug('--')
            MY_LOGGER.debug('type_directory = %s', type_directory)
            images_directory = os.path.join(dates_directory, type_directory)

            for filename in os.listdir(images_directory):
                # date time for the file
                file_age = TIME_NOW - os.path.getmtime(os.path.join(images_directory, filename))
                if file_age > MIN_AGE:
                    MY_LOGGER.debug('DELETE - %s %f %f %f', images_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                    wxcutils.run_cmd('rm ' + images_directory + '/' + filename)
                # else:
                #     MY_LOGGER.debug('keep   - %s %f %f %f', images_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

            # directory may be empty, if so, remove it
            if not os.listdir(dates_directory + '/' + type_directory):
                MY_LOGGER.debug('deleting empty directory - %s', dates_directory + '/' + type_directory)
                wxcutils.run_cmd('rmdir ' + dates_directory + '/' + type_directory)

        # directory may be empty, if so, remove it
        if not os.listdir(dates_directory):
            MY_LOGGER.debug('deleting empty directory - %s', dates_directory)
            wxcutils.run_cmd('rmdir ' + dates_directory)


def process_ews_g1():
    """process EWS-G1 files"""
    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'EWS-G1'
    MY_LOGGER.debug('EWS-G1')
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    for date_directory in find_directories(sat_dir):
        MY_LOGGER.debug('date_directory = %s', date_directory)
        dates_directory = os.path.join(sat_dir, date_directory)

        type_directories = find_directories(dates_directory)
        for type_directory in type_directories:
            MY_LOGGER.debug('--')
            MY_LOGGER.debug('type_directory = %s', type_directory)
            images_directory = os.path.join(dates_directory, type_directory)

            for filename in os.listdir(images_directory):
                # date time for the file
                file_age = TIME_NOW - os.path.getmtime(os.path.join(images_directory, filename))
                if file_age > MIN_AGE:
                    MY_LOGGER.debug('DELETE - %s %f %f %f', images_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                    wxcutils.run_cmd('rm ' + images_directory + '/' + filename)
                # else:
                #     MY_LOGGER.debug('keep   - %s %f %f %f', images_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

            # directory may be empty, if so, remove it
            if not os.listdir(dates_directory + '/' + type_directory):
                MY_LOGGER.debug('deleting empty directory - %s', dates_directory + '/' + type_directory)
                wxcutils.run_cmd('rmdir ' + dates_directory + '/' + type_directory)

        # directory may be empty, if so, remove it
        if not os.listdir(dates_directory):
            MY_LOGGER.debug('deleting empty directory - %s', dates_directory)
            wxcutils.run_cmd('rmdir ' + dates_directory)


def process_electro_l_2():
    """process Electro-L-2 files"""
    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'electro-l-2'
    MY_LOGGER.debug('Electro-L-2')
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    for date_directory in find_directories(sat_dir):
        MY_LOGGER.debug('date_directory = %s', date_directory)
        dates_directory = os.path.join(sat_dir, date_directory)

        type_directories = find_directories(dates_directory)
        for type_directory in type_directories:
            MY_LOGGER.debug('--')
            MY_LOGGER.debug('type_directory = %s', type_directory)
            images_directory = os.path.join(dates_directory, type_directory)

            for filename in os.listdir(images_directory):
                # date time for the file
                file_age = TIME_NOW - os.path.getmtime(os.path.join(images_directory, filename))
                if file_age > MIN_AGE:
                    MY_LOGGER.debug('DELETE - %s %f %f %f', images_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                    # wxcutils.run_cmd('rm ' + images_directory + '/' + filename)
                else:
                    MY_LOGGER.debug('keep   - %s %f %f %f', images_directory + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

            # directory may be empty, if so, remove it
            if not os.listdir(dates_directory + '/' + type_directory):
                MY_LOGGER.debug('deleting empty directory - %s', dates_directory + '/' + type_directory)
                wxcutils.run_cmd('rmdir ' + dates_directory + '/' + type_directory)

        # directory may be empty, if so, remove it
        if not os.listdir(dates_directory):
            MY_LOGGER.debug('deleting empty directory - %s', dates_directory)
            wxcutils.run_cmd('rmdir ' + dates_directory)


def process_sanchez():
    """process Sanchez files"""

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'sanchez'
    MY_LOGGER.debug('Himawari')
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    sat_directories = find_directories(sat_dir)
    for sat_directory in sat_directories:
        # MY_LOGGER.debug('--')
        # MY_LOGGER.debug('sat_directory = %s', sat_directory)
        sat_path = sat_dir  + '/' + sat_directory
        type_directories = find_directories(sat_path)

        for type_directory in type_directories:
            # MY_LOGGER.debug('--')
            # MY_LOGGER.debug('type_directory = %s', type_directory)
            type_path = sat_path  + '/' + type_directory
            view_directories = find_directories(type_path)

            for view_directory in view_directories:
                # MY_LOGGER.debug('--')
                # MY_LOGGER.debug('view_directory = %s', view_directory)
                view_path = type_path  + '/' + view_directory
                view_directories = find_directories(view_path)

                for date_directory in find_directories(view_path):
                    # MY_LOGGER.debug('--')
                    # MY_LOGGER.debug('date_directory = %s', date_directory)
                    date_path = view_path  + '/' + date_directory
                    view_directories = find_directories(date_path)

                    for filename in os.listdir(date_path):
                        # date time for the file
                        file_age = TIME_NOW - os.path.getmtime(os.path.join(date_path, filename))
                        if file_age > MIN_AGE:
                            MY_LOGGER.debug('DELETE - %s %f %f %f', date_path + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)
                            wxcutils.run_cmd('rm ' + date_path + '/' + filename)
                        # else:
                        #     MY_LOGGER.debug('keep   - %s %f %f %f', date_path + '/' + filename, file_age, MIN_AGE, MIN_AGE - file_age)

                    # directory may be empty, if so, remove it
                    if not os.listdir(date_path):
                        MY_LOGGER.debug('deleting empty directory - %s', date_path)
                        wxcutils.run_cmd('rmdir ' + date_path)

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
MODULE = 'tidy'
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

BASEDIR = '/home/pi/goes/'
MY_LOGGER.debug('BASEDIR = %s', BASEDIR)

SANCHEZ_PATH = BASEDIR + 'sanchez/'

# minumum age for files to be deleted > 31 days
MIN_AGE = 31 * 24 * 60 * 60
MY_LOGGER.debug('MIN_AGE = %s', MIN_AGE)

# get current epoch time
TIME_NOW = time.time()
MY_LOGGER.debug('TIME_NOW = %s', TIME_NOW)

# process GOES 17 files
process_goes('17')

# process GOES 16 files
process_goes('16')

# process Himawari 8 files
process_himawari('8')

# process nws files
process_nws()

# process sanchez files
process_sanchez()

# process GK-2A files
process_gk_2a()

# process EWS-G1 files
process_ews_g1()

# process Electro-L-2 files
process_electro_l_2()

# except:
#     MY_LOGGER.critical('Global exception handler: %s %s %s',
#                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
