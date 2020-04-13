#!/usr/bin/env python3
"""wxcapture utility code"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import json
import shutil
from datetime import datetime
import pytz
from tzlocal import get_localzone


FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_UTIL_LOGGER = None


def get_console_handler():
    """Get logger console handler"""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(path, log_file):
    """Get logger file handler"""
    file_handler = TimedRotatingFileHandler(path + log_file, when='midnight', backupCount=7)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name, path, log_file):
    """Create logger"""
    global MY_UTIL_LOGGER
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler(path, log_file))
    logger.propagate = False
    MY_UTIL_LOGGER = logger
    return logger


def run_cmd(tmp_cmd):
    """Run an OS command"""
    MY_UTIL_LOGGER.debug('run_cmd = %s', tmp_cmd)
    os.system(tmp_cmd)


def copy_file(file_source, file_dest):
    """Copy a file"""
    MY_UTIL_LOGGER.debug('copy_file from %s to %s', file_source, file_dest)
    shutil.copy(file_source, file_dest)


def move_file(src_dir, src_file, dest_dir, dest_file):
    """move a file"""
    MY_UTIL_LOGGER.debug('move_file from %s/%s to %s/%s', src_dir, src_file, dest_dir, dest_file)
    shutil.move(os.path.join(src_dir, src_file), os.path.join(dest_dir, dest_file))


def make_directory(directory_name):
    """move a file"""
    MY_UTIL_LOGGER.debug('make_directory %s', directory_name)
    os.mkdir(directory_name)


def load_file(tmp_file_path, tmp_filename):
    """load file from file system"""
    MY_UTIL_LOGGER.debug('load_file from %s %s', tmp_file_path, tmp_filename)
    with open(tmp_file_path + tmp_filename) as tmp_file:
        data = tmp_file.read()
    tmp_file.close()
    MY_UTIL_LOGGER.debug('data = %s', data)
    return data


def save_file(tmp_file_path, tmp_filename, tmp_payload):
    """save file to file system"""
    MY_UTIL_LOGGER.debug('save_file to %s %s', tmp_file_path, tmp_filename)
    with open(tmp_file_path + tmp_filename, 'w') as tmp_file:
        tmp_file.write(tmp_payload)
    tmp_file.close()


def load_json(tmp_file_path, tmp_filename):
    """load json file from file system"""
    MY_UTIL_LOGGER.debug('load_json from %s %s', tmp_file_path, tmp_filename)
    with open(tmp_file_path + tmp_filename) as json_file:
        data = json.load(json_file)
    json_file.close()
    return data


def save_json(tmp_file_path, tmp_filename, data):
    """save json file to the file system"""
    MY_UTIL_LOGGER.debug('save_json to %s %s', tmp_file_path, tmp_filename)
    with open(tmp_file_path + tmp_filename, 'w') as json_file:
        json.dump(data, json_file)
    json_file.close()


def epoch_to_utc(epoch, mask):
    """ convert epoch to UTC"""
    return datetime.fromtimestamp(float(epoch), tz=pytz.utc).strftime(mask)


def epoch_to_local(epoch, mask):
    """ convert epoch to local"""
    return datetime.fromtimestamp(float(epoch)).strftime(mask)


def utc_to_epoch(utc, mask):
    """ convert UTC to epoch"""
    return str((datetime.strptime(utc, mask) -
                datetime(1970, 1, 1)).total_seconds())


def local_to_epoch(local, mask):
    """ convert local to epoch"""
    return datetime.strptime(local, mask).strftime('%s')


def utc_datetime_to_epoch(temp_dt):
    """ convert UTC datetime to epoch"""
    return str((temp_dt - datetime(1970, 1, 1)).total_seconds())


def local_datetime_to_epoch(temp_dt):
    """ convert local datetime to epoch"""
    return temp_dt.strftime('%s')


def epoch_to_datetime_utc(epoch):
    """ convert epoch to UTC datetime"""
    return datetime.fromtimestamp(float(epoch), tz=pytz.utc)


def epoch_to_datetime_local(epoch):
    """ convert epoch to local datetime"""
    return datetime.fromtimestamp(float(epoch), tz=get_localzone())


def utc_to_local(utc, mask):
    """ convert UTC to local"""
    return epoch_to_local(utc_to_epoch(utc, mask), mask)


def local_to_utc(local, mask):
    """ convert local to UTC"""
    return epoch_to_utc(local_to_epoch(local, mask), mask)
