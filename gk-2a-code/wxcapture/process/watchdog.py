#!/usr/bin/env python3
"""Ensure goesrecv is running"""


# import libraries
import subprocess
import platform
import sys
from subprocess import Popen, PIPE
import time
import json
from pynng import Sub0
import wxcutils


def is_running(process_name):
    """see if a process is running"""
    try:
        cmd = subprocess.Popen(('ps', '-ef'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('grep', process_name), stdin=cmd.stdout)
        cmd.wait()
        MY_LOGGER.debug('output = %s', output.decode('utf-8'))
        if output.decode('utf-8').count(process_name) > 1:
            MY_LOGGER.debug('%s is running', process_name)
            return True
    except:
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return False


def number_processes(process_name):
    """see how many processes are running"""
    try:
        cmd = subprocess.Popen(('ps', '-ef'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('grep', CODE_PATH + process_name), stdin=cmd.stdout)
        cmd.wait()
        MY_LOGGER.debug('output = %s', output.decode('utf-8'))
        MY_LOGGER.debug('%s process(es) are running', output.decode('utf-8').count(process_name))
        return output.decode('utf-8').count(process_name)
    except:
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return 0


def is_processing(process_name, minutes):
    """see if images are being created in last defined number of minutes"""
    cmd = Popen(['find', '/home/pi/gk-2a/xrit-rx/received', '-cmin',
                 str(-1 * minutes)], stdout=PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    MY_LOGGER.debug('stdout:%s', stdout.decode('utf-8'))
    MY_LOGGER.debug('stderr:%s', stderr.decode('utf-8'))

    if stdout.decode('utf-8'):
        MY_LOGGER.debug('%s is processing images', process_name)
        return True
    MY_LOGGER.debug('%s is NOT processing images', process_name)

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
        if '/dev/root' in dv_line:
            dv_space = dv_line.split()[4].split('%')[0]
    MY_LOGGER.debug('dv_space  = %s used on %s', dv_space, platform.node())
    wxcutils.save_file(OUTPUT_PATH, 'used-' + platform.node() + '.txt', dv_space)


def sat_validation():
    """validate satellite info"""

    sat_servers = wxcutils.load_json(CONFIG_PATH, 'sat-servers.json')

    result = []
    for sat_server in sat_servers:
        MY_LOGGER.debug('Processing %s', sat_server)
        address = 'tcp://' + sat_server['ip'] + ':' + sat_server['port']

        sub0 = Sub0(dial=address, recv_timeout=100, topics="")

        # make sure everyone is connected
        time.sleep(0.1)

        retry_counter = 1
        op = 'unset'
        while retry_counter <= 10:
            try:
                op = json.loads(sub0.recv().decode("utf-8"))
                result.append({'timestamp' : op['timestamp'],
                               'skipped_symbols' : op['skipped_symbols'],
                               'viterbi_errors' : op['viterbi_errors'],
                               'reed_solomon_errors' : op['reed_solomon_errors'],
                               'ok' : 'Locked' if op['ok'] else 'Unlocked',
                               'label' : sat_server['label'],
                               'when' : str(time.time())})
                break
            except:
                MY_LOGGER.debug('Attempt %d', retry_counter)
                MY_LOGGER.debug('Unexpected error connecting to %s : 0 %s 1 %s 2 %s', address,
                                sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                retry_counter += 1
                MY_LOGGER.debug('Sleeping 2 seconds...')
                time.sleep(2)

        MY_LOGGER.debug('op %s', op)

    MY_LOGGER.debug('result = %s', result)

    # close the socket now we've finished with it
    sub0.close()

    wxcutils.save_json(OUTPUT_PATH, 'satellite-receivers.json', result)


# setup paths to directories
HOME = '/home/pi/'
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
CONFIG_PATH = CODE_PATH + 'config/'
print(CONFIG_PATH)

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

REBOOT = False

# see if anything is not running / processing
if not is_running('goesrecv'):
    MY_LOGGER.debug('goesrecv is not running')
    REBOOT = True

if not is_running('xrit-rx.py'):
    MY_LOGGER.debug('xrit-rx.py is not running')
    REBOOT = True

if not is_processing('goesrecv', 15):
    MY_LOGGER.debug('goesrecv is not processing')
    REBOOT = True

# see if too many find_files.py are running
if number_processes('find_files.py') > 1:
    MY_LOGGER.debug('Too many find_files.py running')
    REBOOT = True

# log drive space free to file
drive_validation()

# validate satellite info
sat_validation()

# sync the output files
wxcutils.run_cmd('rsync -rtPv ' + OUTPUT_PATH + 'used-gamma.txt mike@192.168.100.18:/home/mike/wxcapture/gk-2a')
wxcutils.run_cmd('rsync -rtPv ' + OUTPUT_PATH + 'satellite-receivers.json mike@192.168.100.18:/home/mike/wxcapture/gk-2a')


if REBOOT:
    # reboot the Pi
    MY_LOGGER.debug('rebooting the Pi')
    wxcutils.run_cmd('reboot')
else:
    # All good, no action required
    MY_LOGGER.debug('All good, no action required')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
