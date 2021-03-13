#!/usr/bin/env python3
"""Ensure goesproc is running"""


# import libraries
import os
import subprocess
import platform
from subprocess import Popen, PIPE
import wxcutils


def is_running(process_name):
    """see if a process is running"""
    try:
        cmd = subprocess.Popen(('ps', '-A'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('grep', process_name), stdin=cmd.stdout)
        cmd.wait()
        MY_LOGGER.debug('output = %s', output.decode('utf-8'))
        if process_name in output.decode('utf-8'):
            MY_LOGGER.debug('%s is running', process_name)
            return True
    except:
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return False


def is_processing(process_name, minutes):
    """see if images are being created in last defined number of minutes"""
    cmd = Popen(['find', '/home/pi/goes/goes17', '-cmin', str(-1 * minutes)], stdout=PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    MY_LOGGER.debug('stdout:%s', stdout.decode('utf-8'))
    MY_LOGGER.debug('stderr:%s', stderr.decode('utf-8'))

    if len(stdout.decode('utf-8')) > 0:
        MY_LOGGER.debug('%s is processing images', process_name)
        return True
    MY_LOGGER.debug('%s is NOT processing images', process_name)

    # need to kill off any existing goesproc processes
    # not totally elegent, but should only be one goesproc on a server
    wxcutils.run_cmd('pkill -f ' + process_name)
    return False


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
        if '/home' in dv_line:
            dv_space = dv_line.split()[4].split('%')[0]
    MY_LOGGER.debug('dv_space  = %s used on %s', dv_space, platform.node())
    wxcutils.save_file(OUTPUT_PATH, 'used-' + platform.node() + '.txt', dv_space)


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
MODULE = 'watchdog'
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

# test if goesproc is running or processing
if not is_running('goesproc') or not is_processing('goesproc', 10):
    # need to kick off the code
    MY_LOGGER.debug('Kicking it off')
    wxcutils.run_cmd('goesproc -c /usr/share/goestools/goesproc-goesr.conf -m packet ' +
                     '--subscribe tcp://203.86.195.49:5004 --out /home/pi/goes &')
    if is_running('goesproc'):
        MY_LOGGER.debug('goesproc is now running')
    else:
        MY_LOGGER.critical('goesproc is NOT running and could not be restarted')

# log drive space free to file
drive_validation()

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
