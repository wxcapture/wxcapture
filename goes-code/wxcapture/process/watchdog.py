#!/usr/bin/env python3
"""Ensure goesproc is running"""


# import libraries
import os
import sys
import subprocess
import time
import glob
import platform
from subprocess import Popen, PIPE
from tcping import Ping
import wxcutils


def long_check(lc_process):
    """kill any overly long running processes"""
    MY_LOGGER.debug('-' * 30)
    MY_LOGGER.debug('process = %s, max age = %s', lc_process['Process Name'], lc_process['Max Age'])

    cmd = subprocess.Popen(('ps', '-eo', 'pid,etimes,cmd'), stdout=subprocess.PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    # MY_LOGGER.debug('stdout:%s', stdout.decode('utf-8'))
    MY_LOGGER.debug('stderr:%s', stderr.decode('utf-8'))

    rows = stdout.decode('utf-8').splitlines()
    for row in rows:
        if 'python' in row and lc_process['Process Name'] in row:
            MY_LOGGER.debug('row = %s', row)
            bits = row.split()
            if int(bits[1]) > int(lc_process['Max Age']) * 60:
                MY_LOGGER.debug('Process too old, need to kill')
                wxcutils.run_cmd('kill '+ bits[0])


def validate_sat(vs):
    """validate if sat files received"""
    new_status = 'ERROR'
    status_change = '???'
    current_age = "n/a"

    search = FILE_BASE + vs['Location'] + '/**/*'
    MY_LOGGER.debug('search = %s', search)

    try:
        list_of_files = glob.glob(search, recursive=True)
        latest_file = max(list_of_files, key=os.path.getctime)
        MY_LOGGER.debug('latest_file = %s', latest_file)
        current_age = str(int((time.time() - os.path.getctime(latest_file)) / 60))
        MY_LOGGER.debug('age = %s', current_age)
        MY_LOGGER.debug('max age = %s', vs['Max Age'])
        if int(current_age) > int(vs['Max Age']):
            new_status = 'ERROR'
        else:
            new_status = 'OK'
    except:
        MY_LOGGER.debug('Exception whilst searching, using defaults')

    if new_status != vs['Last Status']:
        status_change = 'Y'
    else:
        status_change = 'N'

    return new_status, status_change, current_age


def test_connection(network_connection, attempt, timeout):
    """test if we have connectivity"""
    def try_connect():
        """try the connection"""
        MY_LOGGER.debug('-' * 4)
        tc_status = ''
        try:
            ping.ping(attempt)
            result = ''.join(ping.result.raw)
            MY_LOGGER.debug('result = %s', result)
            if str(attempt) + ' successed' in result:
                MY_LOGGER.debug('Connection is active - OK')
                tc_status = 'OK'
                MY_LOGGER.debug('-' * 4)
                return tc_status
            elif str(attempt) + ' failed' in result:
                MY_LOGGER.debug('Connection timed out - ERROR')
                tc_status = 'Time out'
            else:
                MY_LOGGER.error('Connection is not active - ERROR')
                tc_status = 'Not active'
        except ConnectionRefusedError:
            MY_LOGGER.error('Connection refused when trying to connect - ERROR')
            MY_LOGGER.critical('test_connection - Connection refused - exception handler: %s | %s | %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            tc_status = 'Connection refused'
        except OSError as error_message:
            MY_LOGGER.error('Connection OS error %s - ERROR', error_message)
            MY_LOGGER.critical('test_connection - OS Error - exception handler: %s | %s | %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
            tc_status = 'Connection OS Error'
        MY_LOGGER.debug('-' * 4)
        return tc_status


    MY_LOGGER.debug('-' * 20)
    MY_LOGGER.debug('Test connection - %s', network_connection)

    ping = Ping(network_connection['ip'], network_connection['port'], timeout)

    status = try_connect()

    return status


def is_running(process_name):
    """see if a process is running"""
    try:
        cmd = subprocess.Popen(('ps', '-ef'), stdout=subprocess.PIPE)
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


def is_processing(process_name, minutes, sat):
    """see if images are being created in last defined number of minutes"""
    MY_LOGGER.debug('Validating processing against %s', sat)
    cmd = Popen(['find', FILE_BASE + sat, '-cmin', str(-1 * minutes)], stdout=PIPE, stderr=PIPE)
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
        if '/dev/sda1' in dv_line:
            MY_LOGGER.debug('used for / - %s', dv_stdout)
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

# load config
NETCONFIG = wxcutils.load_json(OUTPUT_PATH, 'network.json')
MY_LOGGER.debug('attempt = %s', NETCONFIG['attempt'])
MY_LOGGER.debug('timeout = %s', NETCONFIG['timeout'])

FILE_BASE = '/home/pi/goes/'
MY_LOGGER.debug('FILE_BASE = %s', FILE_BASE)

# test for network connectivity
for key, value in NETCONFIG.items():
    if key == 'addresses':
        for nc in NETCONFIG[key]:
            if nc['Active'] == 'yes':
                MY_LOGGER.debug('-' * 20)
                MY_LOGGER.debug(nc)
                # need to fix updating the NETCONFIG part!
                nc['status'] = test_connection(nc, NETCONFIG['attempt'], NETCONFIG['timeout'])
                nc['when'] = time.time()
wxcutils.save_json(OUTPUT_PATH, 'network.json', NETCONFIG)

# test if goesproc is running or processing
if not is_running('goesproc') or not is_processing('goesproc', 10, 'goes18'):
    # need to kick off the code
    MY_LOGGER.debug('Kicking it off')
    # original version
    # wxcutils.run_cmd('goesproc -c /usr/share/goestools/goesproc-goesr.conf -m packet ' +
    #                  '--subscribe tcp://203.86.195.49:5004 --out /home/pi/goes &')
    # updated version
    wxcutils.run_cmd('goesproc -c /usr/share/goestools/NEWgoesproc-goesr.conf -m packet ' +
                     '--subscribe tcp://203.86.195.49:5004 --out /home/pi/goes &')
    if is_running('goesproc'):
        MY_LOGGER.debug('goesproc is now running')
    else:
        MY_LOGGER.critical('goesproc is NOT running and could not be restarted')

# log drive space free to file
drive_validation()

# test if tweet.py is running, if not kick it off
MY_LOGGER.debug('=' * 20)
if not is_running('tweet.py'):
    # need to kick off the code
    MY_LOGGER.debug('tweet.py not running - kicking it off')
    wxcutils.run_cmd(CODE_PATH + 'tweet.py &')
else:
    MY_LOGGER.debug('tweet.py is running')

# test if images received for all sats
SATCONFIG = wxcutils.load_json(CONFIG_PATH, 'last-received.json')
# iterate through satellites
for sc in SATCONFIG:
    MY_LOGGER.debug('-' * 20)
    MY_LOGGER.debug('Processing - %s', sc['Display Name'])
    if sc['Active'] == 'yes':
        MY_LOGGER.debug('Active - Validation processing')
        # do the validation
        sc['Last Status'], sc['Status Change'], sc['Current Age'] = validate_sat(sc)
        MY_LOGGER.debug('sc = %s', sc)
    else:
        MY_LOGGER.debug('Inactive - skipping')
# save results
wxcutils.save_json(CONFIG_PATH, 'last-received.json', SATCONFIG)
wxcutils.save_json(OUTPUT_PATH, 'last-received.json', SATCONFIG)

# find overly long running processes to kill them
PSCONFIG = wxcutils.load_json(CONFIG_PATH, 'running.json')
for process in PSCONFIG:
    long_check(process)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
