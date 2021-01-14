#!/usr/bin/env python3
"""backup servers

options are:
Backup everything (slow)
    ./backup.py ALL
Backup since last backup
    ./backup.py NEW
"""


# import libraries
import os
import sys
import glob
import subprocess
from datetime import datetime, timezone, timedelta
from subprocess import Popen, PIPE
import wxcutils


def do_rsync(dr_params, dr_exclude, dr_source, dr_output):
    """do the rsync"""
    MY_LOGGER.debug('Doing rsync: options = %s, exclude = %s, source = %s, output = %s',
                    dr_params, dr_exclude, dr_source, dr_output)
    # run rsync, waiting for completion
    if not dr_exclude:
        cmd = Popen(['rsync', '-' + dr_params, dr_source, dr_output], stdout=PIPE, stderr=PIPE)
    else:
        cmd = Popen(['rsync', '-' + dr_params, '--exclude', '\'' + dr_exclude + '\'', dr_source, dr_output], stdout=PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    MY_LOGGER.debug('stdout:%s', stdout)
    MY_LOGGER.debug('stderr:%s', stderr)


def do_backup_all():
    """backup everything (slow)"""
    MY_LOGGER.debug('Backing up everything')

    MY_LOGGER.debug('GK-2A')
    # do_rsync('caWv', '', 'pi@192.168.100.7:/home/pi/gk-2a/xrit-rx/received/LRIT/', '/mnt/f/Satellites/gk-2a/LRIT/')

    MY_LOGGER.debug('NWS')
    # do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/nwsdata/', '/mnt/f/Satellites/nwsdata/')

    MY_LOGGER.debug('GOES 16')
    # do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/goes16/', '/mnt/f/Satellites/goes16/')

    MY_LOGGER.debug('GOES 17')
    # do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/goes17/', '/mnt/f/Satellites/goes17/')

    MY_LOGGER.debug('Himawari 8')
    # do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/himawari8/', '/mnt/f/Satellites/himawari8/')

    MY_LOGGER.debug('Website')
    # do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/', '/mnt/f/kiwiweather/')


def get_today():
    """get today as a datetime object"""
    # note that this is the UTC date / time
    # sat image times are stored based on UTC time
    return datetime.utcnow()


def get_last_backup_data():
    """load last backup data"""
    return wxcutils.load_json(CONFIG_PATH, 'last_backup.json')


def save_last_backup_data():
    """dave last backup data"""
    wxcutils.save_json(CONFIG_PATH, 'last_backup.json', LAST_BACKUP_DATA)


def daterange(start_date, end_date):
    """get a date range between two dates"""
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def do_backup_new():
    """backup since the day of the last backup"""
    MY_LOGGER.debug('Backing up ince the day of the last backup')

    # UTC date for the last backup
    MY_LOGGER.debug('Last backup date = %s', LAST_BACKUP_DATA['last backup date'])
    bits = LAST_BACKUP_DATA['last backup date'].split('-')
    utc_date_last = datetime(int(bits[0]),
                             int(bits[1]),
                             int(bits[2]),
                             0, 0, 0, 0)
    MY_LOGGER.debug('Last backup date (dt) = %s', utc_date_last)

    # current UTC date
    utc_date_now = datetime.utcnow()
    MY_LOGGER.debug('Current UTC date (YYYY-MM=DD) = %s', str(utc_date_now.year) + '-' + str(utc_date_now.month) + '-' + str(utc_date_now.day))

    # round up the hours / min / seconds / microsecond
    # need to do this to get all of today
    utc_date_now = utc_date_now.replace(hour=23, minute=59, second=59, microsecond=999999)
    # add one day so the date range loops include the last (current) day
    utc_date_now += timedelta(days=1)
    MY_LOGGER.debug('Current UTC date = %s', utc_date_now)

    MY_LOGGER.debug('GK-2A')
    # get all dates between the ranges
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y%m%d")
        MY_LOGGER.debug('date = %s', date_dir)
        do_rsync('caWv', '',
                 'pi@192.168.100.7:/home/pi/gk-2a/xrit-rx/received/LRIT/' + date_dir + '/',
                 '/mnt/f/Satellites/gk-2a/LRIT/' + date_dir + '/')

    # MY_LOGGER.debug('NWS')
   # get all dates between the ranges
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y/%m/%d")
        MY_LOGGER.debug('date = %s', date_dir)
        do_rsync('caWv', '',
                 'pi@192.168.100.15:/home/pi/goes/nwsdata/' + date_dir + '/',
                 '/mnt/f/Satellites/nwsdata/' + date_dir + '/')

    MY_LOGGER.debug('GOES 16')
    directories = ['fd/ch13', 'fd/ch13_enhanced']
    # get all dates between the ranges
    for dir in directories:
        MY_LOGGER.debug('Directory = %a', dir)
        for single_date in daterange(utc_date_last, utc_date_now):
            date_dir = single_date.strftime("%Y-%m-%d")
            MY_LOGGER.debug('date = %s', date_dir)
            do_rsync('caWv', '',
                    'pi@192.168.100.15:/home/pi/goes/goes16/' + dir + '/' + date_dir + '/',
                    '/mnt/f/Satellites/goes16/' + dir + '/' + date_dir + '/')

    MY_LOGGER.debug('GOES 17')
    directories = ['fd/ch02', 'fd/ch07', 'fd/ch08', 'fd/ch09', 'fd/ch13', 'fd/ch14', 'fd/ch15', 'fd/fc',
                   'm1/ch02', 'm1/ch07', 'm1/ch13', 'm1/fc',
                   'm2/ch02', 'm2/ch07', 'm2/ch13', 'm2/fc']

    for dir in directories:
        MY_LOGGER.debug('Directory = %a', dir)
        # get all dates between the ranges
        for single_date in daterange(utc_date_last, utc_date_now):
            date_dir = single_date.strftime("%Y-%m-%d")
            MY_LOGGER.debug('date = %s', date_dir)
            
            do_rsync('caWv', '',
                    'pi@192.168.100.15:/home/pi/goes/goes17/' + dir + '/' + date_dir + '/',
                    '/mnt/f/Satellites/goes17/' + dir + '/' + date_dir + '/')

    MY_LOGGER.debug('Himawari 8')
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y-%m-%d")
        MY_LOGGER.debug('date = %s', date_dir)
        
        do_rsync('caWv', '',
                'pi@192.168.100.15:/home/pi/goes/himawari8/fd/' + date_dir + '/',
                '/mnt/f/Satellites/himawari8/fd/' + date_dir + '/')


    MY_LOGGER.debug('Website')
    # copy over the date range of directories
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y/%m/%d/")
        MY_LOGGER.debug('date = %s', date_dir)
        do_rsync('caWv', '',
        'mike@192.168.100.18:/home/websites/wxcapture/' + date_dir, '/mnt/f/kiwiweather/' + date_dir)

    # copy over elements of the website with user content
    # note that copying everything is very slow and it has a
    # significant impact on website performance
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.html', '/mnt/f/kiwiweather/*.html')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/.htaccess', '/mnt/f/kiwiweather/.htaccess')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.json', '/mnt/f/kiwiweather/*.json')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.csv', '/mnt/f/kiwiweather/*.csv')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.php', '/mnt/f/kiwiweather/*.php')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.png', '/mnt/f/kiwiweather/*.png')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.txt', '/mnt/f/kiwiweather/*.txt')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/css/', '/mnt/f/kiwiweather/css/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/gk-2a/', '/mnt/f/kiwiweather/gk-2a/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/goes/', '/mnt/f/kiwiweather/goes/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/images/', '/mnt/f/kiwiweather/images/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/js/', '/mnt/f/kiwiweather/js/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/lightbox/', '/mnt/f/kiwiweather/lightbox/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/sensors/', '/mnt/f/kiwiweather/sensors/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/.html/', '/mnt/f/kiwiweather/.html/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/.json/', '/mnt/f/kiwiweather/.json/')
    do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/.php/', '/mnt/f/kiwiweather/.php/')
    
    # not backed up are:
    # wp-admin
    # wp-content
    # wp-includes

    # DO NOT USE
    # performance very slow plus significant impact on website performance
    # potentially need to exclude some directory(s)?
    # do_rsync('caWv', '2*',
    #          'mike@192.168.100.18:/home/websites/wxcapture/', '/mnt/f/kiwiweather/')
    # DO NOT USE


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'web/'
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


try:
    # extract parameters
    BACKUP_TYPE = sys.argv[1].upper()
    MY_LOGGER.debug('backup type = %s', BACKUP_TYPE)

except IndexError as exc:
    MY_LOGGER.critical('Must use ALL or NEW as a parameter')
    # re-throw it as this is fatal
    raise

if BACKUP_TYPE == 'ALL':
    LAST_BACKUP_DATA = get_last_backup_data()
    TODAY = get_today()
    do_backup_all()
    LAST_BACKUP_DATA['last backup date'] = str(TODAY.year) + '-' + str(TODAY.month) + '-' + str(TODAY.day)
    save_last_backup_data()
else:
    LAST_BACKUP_DATA = get_last_backup_data()
    TODAY = get_today()

    if not LAST_BACKUP_DATA['last backup date']:
        MY_LOGGER.debug('No last backup yet performed')
        MY_LOGGER.debug('You MUST do a full backup first')
    else:
        do_backup_new()
        LAST_BACKUP_DATA['last backup date'] = str(TODAY.year) + '-' + str(TODAY.month) + '-' + str(TODAY.day)
        save_last_backup_data()

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
