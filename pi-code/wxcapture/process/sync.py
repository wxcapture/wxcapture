#!/usr/bin/env python3
"""update weather.tle file hourly"""


# import libraries
import os
import sys
import glob
import platform
from subprocess import Popen, PIPE
import wxcutils


def drive_validation():
    """validate drive space utilisation"""
    dv_errors_found = False
    dv_space = 'unknown'

    dv_cmd = Popen(['df'], stdout=PIPE, stderr=PIPE)
    dv_stdout, dv_stderr = dv_cmd.communicate()
    MY_LOGGER.debug('stdout:%s', dv_stdout)
    MY_LOGGER.debug('stderr:%s', dv_stderr)
    dv_results = dv_stdout.decode('utf-8').splitlines()
    for dv_line in dv_results:
        if '/dev/root' in dv_line:
            dv_space = dv_line.split()[4].split('%')[0]
    MY_LOGGER.debug('dv_space  = %s used on %s', dv_space, platform.node())
    dv_filename = 'used-' + platform.node() + '.txt'
    wxcutils.save_file(OUTPUT_PATH, dv_filename, dv_space)

    # rsync files to server
    MY_LOGGER.debug('rsync: %s', dv_filename)
    wxcutils.run_cmd('rsync -t ' + OUTPUT_PATH + dv_filename + ' ' + RSYNC_CONFIG['remote user'] + '@' + RSYNC_CONFIG['remote host'] + ':' + RSYNC_CONFIG['remote directory'] + '/' + dv_filename)


def process_file(pf_file_name):
    """process a file, moving files to remote server
    using rynch and performing locking"""


    def do_sync(ds_source, ds_destination):
        """synch the file over"""
        MY_LOGGER.debug('rsync %s %s %s', '-avz', ds_source, ds_destination)
        pf_cmd = Popen(['rsync', '-avz', ds_source, ds_destination], stdout=PIPE, stderr=PIPE)
        pf_stdout, pf_stderr = pf_cmd.communicate()
        pf_stdout = pf_stdout.decode('utf-8')
        pf_stderr = pf_stderr.decode('utf-8')
        MY_LOGGER.debug('stdout:%s', pf_stdout)
        if pf_stderr == '':
            MY_LOGGER.debug('rsync successful')
            return True
        MY_LOGGER.debug('rsync error = %s', pf_stderr)
        return False


    # load the queue file
    pf_file_data = wxcutils.load_json(QUEUE_PATH, pf_file_name)

    # recover the lock_id
    pf_lock_id = pf_file_data['lock']
    MY_LOGGER.debug('pf_lock_id = %s', pf_lock_id)

    # iterate through the files
    for pf_file in pf_file_data['files']:
        if pf_file['copied'] == 'no':
            MY_LOGGER.debug('To copy - %s %s %s %s', pf_file['source path'], pf_file['source file'], pf_file['destination path'], pf_file['copied'])
            pf_result = do_sync(pf_file['source path'] + '/' + pf_file['source file'],
                                RSYNC_CONFIG['remote user'] + '@' + RSYNC_CONFIG['remote host'] + ':' + RSYNC_CONFIG['remote directory'] + '/' + pf_file['destination path'] + '/' + pf_file['source file'] + '.LOCK.' + pf_lock_id)
            if pf_result:
                pf_file['copied'] = 'yes'

    # check if any files left to be copied
    pf_files_to_copy = False
    for pf_file in pf_file_data['files']:
        if pf_file['copied'] == 'no':
            pf_files_to_copy = True
            break
    if pf_files_to_copy:
        MY_LOGGER.debug('Files still to copy')
        MY_LOGGER.debug('Work still to be done, save file for future processing')
        wxcutils.save_json(QUEUE_PATH, pf_file_name, pf_file_data)
    else:
        MY_LOGGER.debug('All files copied over, copy the unlock over')
        pf_unlock_file = pf_lock_id  + '.UNLOCK'
        wxcutils.run_cmd('touch ' + QUEUE_PATH + pf_unlock_file)
        pf_result = do_sync(QUEUE_PATH + pf_unlock_file,
                            RSYNC_CONFIG['remote user'] + '@' + RSYNC_CONFIG['remote host'] + ':' + RSYNC_CONFIG['remote directory'] + '/' + pf_unlock_file)
        if pf_result:
            MY_LOGGER.debug('lock file copied over successfully')
            wxcutils.run_cmd('rm ' + QUEUE_PATH + pf_unlock_file)
            wxcutils.save_json(QUEUE_PATH, pf_file_name, pf_file_data)
            wxcutils.run_cmd('rm ' + QUEUE_PATH + pf_file_name)
        else:
            MY_LOGGER.debug('Work still to be done, save file for future processing')
            wxcutils.save_json(QUEUE_PATH, pf_file_name, pf_file_data)


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
CONFIG_PATH = CODE_PATH + 'config/'
QUEUE_PATH = CODE_PATH + 'queue/'

# start logging
MODULE = 'sync'
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
MY_LOGGER.debug('QUEUE_PATH = %s', QUEUE_PATH)

try:
    # load data for rsync
    RSYNC_CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-rsync.json')

    # log drive space free to file
    drive_validation()

    # check for files to process
    no_files_to_process = True
    for file_name in glob.glob(QUEUE_PATH + '*.json'):
        no_files_to_process = False
        MY_LOGGER.debug('File to process - %s', file_name.replace(QUEUE_PATH, ''))
        process_file(file_name.replace(QUEUE_PATH, ''))

    if no_files_to_process:
        MY_LOGGER.debug('No file(s) to process')

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
