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
    errors = stderr.decode('utf-8')
    MY_LOGGER.debug('stdout:%s', stdout.decode('utf-8'))
    MY_LOGGER.debug('stderr:%s', errors)

    # remove expected errors
    # no such directory happens with difference between UTC and local date, so can ignore
    if 'No such file or directory' in errors:
        errors = ''

    MY_LOGGER.debug('reported errors:%s', errors)
    return errors


def show_errors(se_type, se_errors):
    """show errors from each backup type"""
    found = False
    MY_LOGGER.debug(se_type)
    for error_line in se_errors:
        # only show if errors to report
        if error_line['errors']:
            MY_LOGGER.debug(error_line['type'] + ' - ' + error_line['errors'])
            found - True
    if not found:
        MY_LOGGER.debug('No errors found')
        return False
    MY_LOGGER.critical('*****************************')
    MY_LOGGER.critical('*****************************')
    MY_LOGGER.critical('*       ERRRORS FOUND       *')
    MY_LOGGER.critical('*****************************')
    MY_LOGGER.critical('*****************************')
    return True


def do_backup_all():
    """backup everything (slow)"""
    MY_LOGGER.debug('Backing up everything')
    errors = []

    MY_LOGGER.debug('GK-2A - data')
    errors.append({'type': 'GK-2A', 'errors': do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/gk-2a/', '/mnt/f/Satellites/gk-2a/LRIT/')})

    MY_LOGGER.debug('GK-2A - gamma')
    errors.append({'type': 'GK-2A', 'errors': do_rsync('caWv', '', 'pi@192.168.100.7:/home/pi/gk-2a/xrit-rx/received/LRIT/', '/mnt/f/Satellites/gk-2a/LRIT/')})

    MY_LOGGER.debug('NWS')
    errors.append({'type': 'NWS', 'errors': do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/nwsdata/', '/mnt/f/Satellites/nwsdata/')})

    MY_LOGGER.debug('GOES 16')
    errors.append({'type': 'GOES 16', 'errors': do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/goes16/', '/mnt/f/Satellites/goes16/')})

    MY_LOGGER.debug('GOES 17')
    errors.append({'type': 'GOES 17', 'errors': do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/goes17/', '/mnt/f/Satellites/goes17/')})

    MY_LOGGER.debug('Himawari 8')
    errors.append({'type': 'Himawari 8', 'errors': do_rsync('caWv', '', 'pi@192.168.100.15:/home/pi/goes/himawari8/', '/mnt/f/Satellites/himawari8/')})



    MY_LOGGER.debug('NOAA / Meteor / ISS')
    errors.append({'type': 'NOAA / Meteor / ISS - data', 'errors': do_rsync('caWv', '',
                                                                            'pi@192.168.100.9:/home/pi/wxcapture/output/',
                                                                            '/mnt/f/Satellites/NOAA-Meteor-ISS/pi/output/')})
    errors.append({'type': 'NOAA / Meteor / ISS - audio', 'errors': do_rsync('caWv', '',
                                                                             'pi@192.168.100.9:/home/pi/wxcapture/audio/',
                                                                             '/mnt/f/Satellites/NOAA-Meteor-ISS/pi/audio/')})

    MY_LOGGER.debug('Website')
    errors.append({'type': 'Website', 'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/', '/mnt/f/kiwiweather/')})

    if show_errors('Full backup', errors):
        MY_LOGGER.debug('errors detected')
        return True
    MY_LOGGER.debug('no errors detected')
    return False


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
    errors = []

    MY_LOGGER.debug('GK-2A - data')
    # get all dates between the ranges
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y%m%d")
        MY_LOGGER.debug('date = %s', date_dir)
        errors.append({'type': 'GK-2A - data - ' + date_dir,
                       'errors': do_rsync('caWv', '',
                                         'pi@192.168.100.15:/home/pi/goes/gk-2a/' + date_dir + '/',
                                         '/mnt/f/Satellites/gk-2a/LRIT/' + date_dir + '/')})

    MY_LOGGER.debug('GK-2A - gamma')
    # get all dates between the ranges
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y%m%d")
        MY_LOGGER.debug('date = %s', date_dir)
        errors.append({'type': 'GK-2A - gamma - ' + date_dir,
                       'errors': do_rsync('caWv', '',
                                         'pi@192.168.100.7:/home/pi/gk-2a/xrit-rx/received/LRIT/' + date_dir + '/',
                                         '/mnt/f/Satellites/gk-2a/LRIT/' + date_dir + '/')})

    MY_LOGGER.debug('NWS')
    # get all dates between the ranges
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y/%m/%d")
        MY_LOGGER.debug('date = %s', date_dir)
        errors.append({'type': 'NWS - ' + date_dir,
                       'errors': do_rsync('caWv', '',
                                          'pi@192.168.100.15:/home/pi/goes/nwsdata/' + date_dir + '/',
                                          '/mnt/f/Satellites/nwsdata/' + date_dir + '/')})

    MY_LOGGER.debug('GOES 16')
    directories = ['fd/ch13', 'fd/ch13_enhanced']
    # get all dates between the ranges
    for dir in directories:
        MY_LOGGER.debug('Directory = %a', dir)
        for single_date in daterange(utc_date_last, utc_date_now):
            date_dir = single_date.strftime("%Y-%m-%d")
            MY_LOGGER.debug('date = %s', date_dir)
            errors.append({'type': 'GOES 16 - ' + dir + ' - ' + date_dir,
                           'errors': do_rsync('caWv', '',
                                              'pi@192.168.100.15:/home/pi/goes/goes16/' + dir + '/' + date_dir + '/',
                                              '/mnt/f/Satellites/goes16/' + dir + '/' + date_dir + '/')})

    MY_LOGGER.debug('GOES 16 Sanchez Data')
    directories = ['fd/ch13']

    for dir in directories:
        MY_LOGGER.debug('Directory = %a', dir)
        # get all dates between the ranges
        for single_date in daterange(utc_date_last, utc_date_now):
            date_dir = single_date.strftime("%Y-%m-%d")
            MY_LOGGER.debug('date = %s', date_dir)
            
            errors.append({'type': 'GOES 16 Sanchez - ' + dir + ' - ' + date_dir,
                           'errors': do_rsync('caWv', '',
                                              'pi@192.168.100.15:/home/pi/goes/sanchez/goes16/' + dir + '/' + date_dir + '/',
                                              '/mnt/f/Satellites/sanchez/goes16/' + dir + '/' + date_dir + '/')})


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
            errors.append({'type': 'GOES 17 - ' + dir + ' - ' + date_dir,
                           'errors': do_rsync('caWv', '',
                                              'pi@192.168.100.15:/home/pi/goes/goes17/' + dir + '/' + date_dir + '/',
                                              '/mnt/f/Satellites/goes17/' + dir + '/' + date_dir + '/')})


    MY_LOGGER.debug('GOES 17 Sanchez Data')
    directories = ['fd/ch13', 'fd/fc']

    for dir in directories:
        MY_LOGGER.debug('Directory = %a', dir)
        # get all dates between the ranges
        for single_date in daterange(utc_date_last, utc_date_now):
            date_dir = single_date.strftime("%Y-%m-%d")
            MY_LOGGER.debug('date = %s', date_dir)
            errors.append({'type': 'GOES 17 Sanchez - ' + dir + ' - ' + date_dir,
                           'errors': do_rsync('caWv', '',
                                              'pi@192.168.100.15:/home/pi/goes/sanchez/goes17/' + dir + '/' + date_dir + '/',
                                              '/mnt/f/Satellites/sanchez/goes17/' + dir + '/' + date_dir + '/')})

    MY_LOGGER.debug('Himawari 8')
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y-%m-%d")
        MY_LOGGER.debug('date = %s', date_dir)
        errors.append({'type': 'Himawari 8 - ' + dir + ' - ' + date_dir,
                       'errors': do_rsync('caWv', '',
                                          'pi@192.168.100.15:/home/pi/goes/himawari8/fd/' + date_dir + '/',
                                          '/mnt/f/Satellites/himawari8/fd/' + date_dir + '/')})

    MY_LOGGER.debug('NOAA / Meteor / ISS')
    # no date selectivity
    errors.append({'type': 'NOAA / Meteor / ISS - data',
                   'errors': do_rsync('caWv', '',
                                      'pi@192.168.100.9:/home/pi/wxcapture/output/',
                                      '/mnt/f/Satellites/NOAA-Meteor-ISS/pi/output/')})
    errors.append({'type': 'NOAA / Meteor / ISS - audio',
                   'errors': do_rsync('caWv', '',
                                      'pi@192.168.100.9:/home/pi/wxcapture/audio/',
                                      '/mnt/f/Satellites/NOAA-Meteor-ISS/pi/audio/')})

    MY_LOGGER.debug('Website')
    # copy over the date range of directories
    for single_date in daterange(utc_date_last, utc_date_now):
        date_dir = single_date.strftime("%Y/%m/%d/")
        MY_LOGGER.debug('date = %s', date_dir)
        errors.append({'type': 'Website - polar' + date_dir,
                        'errors': do_rsync('caWv', '',
                                            'mike@192.168.100.18:/home/websites/wxcapture/' + date_dir, '/mnt/f/kiwiweather/' + date_dir)})

    # copy over elements of the website with user content
    # note that copying everything is very slow and it has a
    # significant impact on website performance
    errors.append({'type': 'Website - html',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.html', '/mnt/f/kiwiweather/')})
    errors.append({'type': 'Website - htaccess',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/.htaccess', '/mnt/f/kiwiweather/.htaccess')})
    errors.append({'type': 'Website - json',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.json', '/mnt/f/kiwiweather/')})
    errors.append({'type': 'Website - csv',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.csv', '/mnt/f/kiwiweather/')})
    errors.append({'type': 'Website - php',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.php', '/mnt/f/kiwiweather/')})
    errors.append({'type': 'Website - png',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.png', '/mnt/f/kiwiweather/')})
    errors.append({'type': 'Website - txt',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/*.txt', '/mnt/f/kiwiweather/')})
    errors.append({'type': 'Website - css',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/css/', '/mnt/f/kiwiweather/css/')})
    errors.append({'type': 'Website - gk-2a',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/gk-2a/', '/mnt/f/kiwiweather/gk-2a/')})
    errors.append({'type': 'Website - goes',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/goes/', '/mnt/f/kiwiweather/goes/')})
    errors.append({'type': 'Website - images',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/images/', '/mnt/f/kiwiweather/images/')})
    errors.append({'type': 'Website - js',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/js/', '/mnt/f/kiwiweather/js/')})
    errors.append({'type': 'Website - lightbox',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/lightbox/', '/mnt/f/kiwiweather/lightbox/')})
    errors.append({'type': 'Website - sensors',
                   'errors': do_rsync('caWv', '', 'mike@192.168.100.18:/home/websites/wxcapture/sensors/', '/mnt/f/kiwiweather/sensors/')})

    
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

    if show_errors('NEW backup', errors):
        MY_LOGGER.debug('errors detected')
        return True
    MY_LOGGER.debug('no errors detected')
    return False


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
    errors_found = do_backup_all()
    LAST_BACKUP_DATA['last backup date'] = str(TODAY.year) + '-' + str(TODAY.month) + '-' + str(TODAY.day)
    if not errors_found:
        MY_LOGGER.debug('Updating last backup date')
        save_last_backup_data()
    else:
        MY_LOGGER.debug('NOT updating last backup date due to errors')
else:
    LAST_BACKUP_DATA = get_last_backup_data()
    TODAY = get_today()

    if not LAST_BACKUP_DATA['last backup date']:
        MY_LOGGER.debug('No last backup yet performed')
        MY_LOGGER.debug('You MUST do a full backup first')
    else:
        errors_found = do_backup_new()
        LAST_BACKUP_DATA['last backup date'] = str(TODAY.year) + '-' + str(TODAY.month) + '-' + str(TODAY.day)
        if not errors_found:
            MY_LOGGER.debug('Updating last backup date')
            save_last_backup_data()
        else:
            MY_LOGGER.debug('NOT updating last backup date due to errors')
MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
