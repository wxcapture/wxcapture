#!/usr/bin/env python3
"""sync Electro L-2 satellite data"""


# import libraries
import os
import sys
import time
import subprocess
from ftplib import FTP
from datetime import datetime, timezone
import pytz
import wxcutils


def number_processes(process_name):
    """see how many processes are running"""
    try:
        cmd = subprocess.Popen(('ps', '-ef'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('grep', process_name), stdin=cmd.stdout)
        cmd.wait()
        MY_LOGGER.debug('output = %s', output.decode('utf-8'))
        process_count = 0
        lines = output.decode('utf-8').splitlines()
        for line in lines:
            if 'grep' in line or '/bin/bash' in line:
                # ignore grep or cron lines
                process_count += 0
            else:
                process_count += 1
        MY_LOGGER.debug('%d process(es) are running', process_count)
        return process_count
    except:
        # note this should not be possible!
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return 0


def mk_dir(directory):
    """only create if it does not already exist"""
    MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


def get_directory_list():
    """get the list of files / directories"""
    store = []
    ftp.retrlines('LIST', callback=store.append)
    return_value = list((line.rsplit(None, 1)[1] for line in store))
    store.clear()
    return return_value


def month_string_to_number(string):
    """decode month name to month number"""
    months = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr':4,
        'may':5,
        'jun':6,
        'jul':7,
        'aug':8,
        'sep':9,
        'oct':10,
        'nov':11,
        'dec':12
        }
    month_short = string.strip()[:3].lower()

    try:
        out = months[month_short]
        return out
    except:
        raise ValueError('Not a month')


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %Y %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %Y %H:%M')


def get_last_generated_text(lgt_filename):
    """build the last generated text"""
    last_generated_text = 'Last generated at ' + get_local_date_time() + ' ' + \
                            LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    MY_LOGGER.debug('last_generated_text = %s - for file %s', last_generated_text, lgt_filename)
    return last_generated_text


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
MODULE = 'electro-l-2'
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

# check if web is already running, if so exit this code
if number_processes('electro-l-2.py') == 1:

    FILE_BASE = '/home/pi/goes/electro-l-2/'
    MY_LOGGER.debug('FILE_BASE = %s', FILE_BASE)

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-2]
    MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

    # get the configuration information
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'electro.json')

    MY_LOGGER.debug('Last sync data - note Moscow date / time, not UTC')
    MY_LOGGER.debug('Last Year = %s', CONFIG_INFO['Last Year'])
    MY_LOGGER.debug('Last Month = %s', CONFIG_INFO['Last Month'])
    MY_LOGGER.debug('Last Day = %s', CONFIG_INFO['Last Day'])
    MY_LOGGER.debug('Last Time = %s', CONFIG_INFO['Last Time'])
    MY_LOGGER.debug('FTP Server Info')
    MY_LOGGER.debug('ftp site = %s', CONFIG_INFO['ftp site'])
    MY_LOGGER.debug('port = %s', CONFIG_INFO['port'])
    MY_LOGGER.debug('username = %s', CONFIG_INFO['username'])
    MY_LOGGER.debug('password = -not logged-')

    # create FTP connection and log in
    ftp = FTP()
    ftp.connect(CONFIG_INFO['ftp site'], int(CONFIG_INFO['port']))
    ftp.login(CONFIG_INFO['username'], CONFIG_INFO['password'])

    # get the welcome message
    MY_LOGGER.debug('welcome message = %s', ftp.getwelcome())

    # go to the correct satellite
    ftp.cwd('ELECTRO_L_2')
    MY_LOGGER.debug('current directory = %s', ftp.pwd())

    # get last processed info
    last_year = ''
    last_month = ''
    last_day = ''
    last_time = ''

    # get list of years
    year_list = get_directory_list()

    for year in year_list:
        MY_LOGGER.debug('year = %s', year)
        # if year is >= last year processed
        if int(year) >= int(CONFIG_INFO['Last Year']):
            MY_LOGGER.debug('Process year = %s', year)
            year_only = False
            if int(year) > int(CONFIG_INFO['Last Year']):
                year_only = True
                MY_LOGGER.debug('year only - new year!')
            # change directory to the year
            ftp.cwd(year)
            MY_LOGGER.debug('current directory = %s', ftp.pwd())
            month_list = get_directory_list()
            for month in month_list:
                MY_LOGGER.debug('month = %s', month)
                # ensure it is a valid month directory - to avoid random directory names
                if month[:3].lower() in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
                    month_number = month_string_to_number(month)
                    # MY_LOGGER.debug('month = %s, number = %d', month, month_number)
                    # process month if in current year and >= last month processed
                    if month_number >= int(CONFIG_INFO['Last Month']) or year_only:
                        MY_LOGGER.debug('Process month = %s', month_number)
                        month_only = False
                        if month_number > int(CONFIG_INFO['Last Month']) or year_only:
                            month_only = True
                            MY_LOGGER.debug('month only')
                        # change directory to the month
                        ftp.cwd(month)
                        MY_LOGGER.debug('current directory = %s', ftp.pwd())
                        day_list = get_directory_list()
                        for day in day_list:
                            MY_LOGGER.debug('day = %s', day)
                            # process day if in current month and >= last day processed
                            if int(day) >= int(CONFIG_INFO['Last Day']) or month_only:
                                MY_LOGGER.debug('Process day = %s', day)
                                day_only = False
                                if int(day) > int(CONFIG_INFO['Last Day']) or month_only:
                                    day_only = True
                                    MY_LOGGER.debug('day only')
                                # create directories, if it does not exist
                                mk_dir(FILE_BASE + year + str(month_number).zfill(2) + day)
                                for channel_directory in ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'RGB']:
                                    mk_dir(FILE_BASE + year + str(month_number).zfill(2) + day + '/' + channel_directory)
                                # change directory to the day
                                ftp.cwd(day)
                                MY_LOGGER.debug('current directory = %s', ftp.pwd())
                                time_list = get_directory_list()
                                for time_value in time_list:
                                    # MY_LOGGER.debug('time_value = %s', time_value)
                                    # process time if in current day and >= last time processed
                                    if int(time_value) >= int(CONFIG_INFO['Last Time']) or day_only:
                                        MY_LOGGER.debug('Process time = %s', time_value)
                                        # change directory to the time
                                        ftp.cwd(time_value)
                                        MY_LOGGER.debug('current directory = %s', ftp.pwd())
                                        # can now process files!
                                        image_list = get_directory_list()
                                        for image in image_list:
                                            # MY_LOGGER.debug('image = %s', image)
                                            if '.jpg' in image:
                                                channel = image.split('.')[0]
                                                channel_bits = channel.split('_')
                                                image_date = '20' + channel_bits[0]
                                                image_time = channel_bits[1]
                                                channel = channel_bits[2]
                                                # only want channels 1 to 9
                                                if channel in ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'RGB']:
                                                    MY_LOGGER.debug('Get image = %s, channel = %s, date = %s, time = %s', image, channel, image_date, image_time)

                                                    # format to align with the sanchez parser
                                                    filename = 'electro-l-2-' + image_date[2:] + '_' + image_time + '_' + channel + '.jpg'
                                                    
                                                    MY_LOGGER.debug('image_date = %s image_time = %s filename - %s', image_date, image_time, filename)

                                                    # see if file already exists
                                                    file_location = FILE_BASE + image_date + '/' + channel + '/' + filename
                                                    if not os.path.exists(file_location):
                                                        # get file
                                                        MY_LOGGER.debug('Getting %s -> %s', image, file_location)
                                                        with open(file_location, 'wb') as f:
                                                            ftp.retrbinary('RETR %s' % image, f.write)
                                                        last_year = year
                                                        last_month = month_number
                                                        last_day = day
                                                        last_time = time_value
                                                        # save a thumbnail of a channel 1 image to send to webserver
                                                        if channel == 'RGB':
                                                            wxcutils.copy_file(FILE_BASE + image_date + '/' + channel + '/' + filename, OUTPUT_PATH + 'electro-l-2-rgb.jpg')

                                                            # create file with date time info
                                                            MY_LOGGER.debug('Writing out last generated date file')
                                                            wxcutils.save_file(OUTPUT_PATH, 'electro-l-2-rgb.txt', get_last_generated_text(filename))
                                                    else:
                                                        MY_LOGGER.debug('File already downloaded')

                                        # end of time, go up a directory
                                        ftp.cwd('..')
                                        MY_LOGGER.debug('current directory = %s', ftp.pwd())

                                # end of day, go up a directory
                                ftp.cwd('..')
                                MY_LOGGER.debug('current directory = %s', ftp.pwd())

                        # end of month, go up a directory
                        ftp.cwd('..')
                        MY_LOGGER.debug('current directory = %s', ftp.pwd())
                else:
                    MY_LOGGER.debug('invalid month = %s', month)

            # end of year, go up a directory
            ftp.cwd('..')
            MY_LOGGER.debug('current directory = %s', ftp.pwd())


    # close connection
    ftp.quit()

    # update config file with latest processed info
    # only if files were processed
    if last_year:
        CONFIG_INFO['Last Year'] = last_year
        CONFIG_INFO['Last Month'] = last_month
        CONFIG_INFO['Last Day'] = last_day
        CONFIG_INFO['Last Time'] = last_time
        wxcutils.save_json(CONFIG_PATH, 'electro.json', CONFIG_INFO)

else:
    MY_LOGGER.debug('Another instance of electro-l-2.py is already running')
    MY_LOGGER.debug('Skip running this instance to allow the existing one to complete')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
