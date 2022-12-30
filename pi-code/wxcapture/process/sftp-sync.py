#!/usr/bin/env python3
"""sync meteor satellite data"""


# import libraries
import os
import sys
import subprocess
from subprocess import Popen, PIPE
import os
import socket
import sys
import traceback
import pytz
from datetime import datetime
import time
import paramiko
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


def convert_to_utc(timestamp_string, mask, timezone):
    """convert to UTC"""

    local_tz = pytz.timezone(timezone)
    ts = datetime.strptime(timestamp_string, mask)
    ts = local_tz.localize(ts)
    ts = str(ts.astimezone(pytz.utc))[0:19]
    MY_LOGGER.debug('UTC timestamp is: {}'.format(ts))
    return ts


def remote_to_local(dir_name):
    """remote to local sync"""

    MY_LOGGER.debug('Syncing %s/Outbound remote to local', dir_name)

    # list files on the remote host
    MY_LOGGER.debug('get file list')
    file_listing = sftp.listdir(dir_name + '/Outbound')
    # MY_LOGGER.debug('file_listing = %s', file_listing)

    # look for .wav files that:
    # start with the upper case of the directory name
    # end with .wav
    for entry in file_listing:
        if entry[-4:] == '.wav' and entry[:len(dir_name)] == dir_name.upper():
            # see if file already exists in AUDIO_PATH
            if not os.path.exists(AUDIO_PATH + entry):
                MY_LOGGER.debug('May need to sync file %s', entry)

                # need to kick off processing images based on .wav file and appropriate tle file
                # see if we need to sync, based on file aged and if not yet synced
                # find tle file for the same day
                # NOAA-18-20221227-235123.wav or METEOR-M-2-20221220-060619.wav
                if dir_name == 'Meteor':
                    syd_date_time = entry[11:26]
                else:
                    syd_date_time = entry[8:23]
                MY_LOGGER.debug('AU Syd date / time = %s', syd_date_time)
                
                tle_utc = convert_to_utc(syd_date_time, '%Y%m%d-%H%M%S', 'Australia/Sydney')
                MY_LOGGER.debug('tle_utc = %s', tle_utc)

                # only process if not "too old"
                time_now_epoch = int(time.time())
                MY_LOGGER.debug('time_now_epoch = %d', time_now_epoch)

                tle_epoch = wxcutils.utc_to_epoch(tle_utc, '%Y-%m-%d %H:%M:%S')
                MY_LOGGER.debug('tle_epoch = %s', tle_epoch)
                MY_LOGGER.debug('tle_epoch = %d', int(float(tle_epoch)))
                age = time_now_epoch - int(float(tle_epoch))
                MY_LOGGER.debug('age = %d', age)

                if age > MAX_AGE:
                    MY_LOGGER.debug('File %s is too old to sync', entry)

                else:
                    MY_LOGGER.debug('File %s is young enough to sync and does not yet exist - syncing', entry)
                    # get file
                    sftp.get(dir_name + '/Outbound/' + entry, AUDIO_PATH + entry)

                    # find nearest time tle
                    # could match on sat name, but best to get the nearest tle
                    # could also match on year / month / day, but there are passes just after midnight
                    # which will be in a later day, but also potentially a later month / year
                    tle_files = []
                    local_file_listing = os.listdir(OUTPUT_PATH)
                    for local_file in local_file_listing:
                        if local_file[-4:] == '.tle':
                            tle_files.append(local_file)
                    tle_files.append(tle_utc.replace(' ', '-').replace(':', '-') + 'FILE-TO-MATCH')
                    tle_files.sort()
                    MY_LOGGER.debug('Sorted list = %s', tle_files)

                    # pick the tle just before the one from Sydney, as this will be either the same or the next pass
                    tle_to_use = 'ERROR'
                    for tle_file in tle_files:
                        if 'FILE-TO-MATCH' in tle_file:
                            break
                        else:
                            tle_to_use = tle_file
                    MY_LOGGER.debug('tle file to use = %s', tle_to_use)

                    # meteor
                    if dir_name == 'Meteor':
                        MY_LOGGER.debug('Processing a Meteor .wav file')
                        # create .s file from the .wav file
                        filename_base = entry.replace('.wav', '')
                        MY_LOGGER.debug('Creating .qpsk file %s', filename_base + '.qpsk')
                        wxcutils.run_cmd('echo yes | /usr/local/bin/meteor_demod -B -r 72000 -m qpsk -o ' +
                                        WORKING_PATH + filename_base + '.qpsk ' + AUDIO_PATH + entry)

                        # run meteordemod
                        MY_LOGGER.debug('run meteordemod')
                        date_dmy = tle_utc[8:10] + '-' + tle_utc[5:7] + '-' + tle_utc[:4]
                        wxcutils.run_cmd('meteordemod -i ' + WORKING_PATH + filename_base + '.qpsk -t ' +
                                        OUTPUT_PATH + tle_to_use + ' -f jpg -d ' +
                                        date_dmy + ' -o ' + MD_WORKING_PATH)

                        # tidy up
                        MY_LOGGER.debug('remove .qspk file')
                        wxcutils.run_cmd('rm ' + WORKING_PATH + filename_base + '.qpsk')

                        # * re-run last locally received meteor
                        # look for Meteor .txt files
                        txt_files = []
                        local_file_listing = os.listdir(OUTPUT_PATH)
                        for local_file in local_file_listing:
                            if local_file[-4:] == '.txt' and 'METEOR' in local_file:
                                txt_files.append(local_file)
                        txt_files.append(tle_utc.replace(' ', '-').replace(':', '-') + 'FILE-TO-MATCH')
                        txt_files.sort()
                        MY_LOGGER.debug('Sorted list = %s', txt_files)

                        # pick the txt just before the one from Sydney, as this will be either the same or the next pass
                        txt_to_use = 'ERROR'
                        for txt_file in txt_files:
                            if 'FILE-TO-MATCH' in txt_file:
                                break
                            else:
                                txt_to_use = txt_file
                        MY_LOGGER.debug('txt file to use = %s', txt_to_use)
                        reprocess_cmd = wxcutils.load_file(OUTPUT_PATH, txt_to_use.replace('./', ''))
                        wxcutils.run_cmd(reprocess_cmd)
                    else:
                        MY_LOGGER.debug('Unknown directory / satellite type')


def local_to_remote(dir_name):
    """local to remote sync"""

    MY_LOGGER.debug('Syncing local to remote %s/Inbound', dir_name)

    # list files on the remote host
    MY_LOGGER.debug('get remote file list')
    remote_file_listing = sftp.listdir(dir_name + '/Inbound')
    # MY_LOGGER.debug('remote_file_listing = %s', remote_file_listing)

    # list local %composite.jpg (Meteor)
    local_file_listing = os.listdir(IMAGE_PATH)
    # MY_LOGGER.debug('local_file_listing = %s', local_file_listing)

    # copy %composite*.jpg files over if not already on remote
    for local_file in local_file_listing:
        if dir_name.upper() in local_file and local_file not in remote_file_listing and local_file[-13:] == 'composite.jpg':
            MY_LOGGER.debug('Need to sync filename = %s', local_file)
            # put file
            sftp.put(IMAGE_PATH + local_file, dir_name + '/Inbound/' + local_file)


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
MD_WORKING_PATH = WORKING_PATH + 'mdtemp/'
CONFIG_PATH = CODE_PATH + 'config/'
AUDIO_PATH = APP_PATH + 'audio/'

# start logging
MODULE = 'sftp-sync'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')
MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('CODE_PATH = %s', CODE_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('OUTPUT_PATH = %s', OUTPUT_PATH)
MY_LOGGER.debug('IMAGE_PATH = %s', IMAGE_PATH)
MY_LOGGER.debug('WORKING_PATH = %s', WORKING_PATH)
MY_LOGGER.debug('MD_WORKING_PATH = %s', MD_WORKING_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# detailed paramiko logging
# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# check if web is already running, if so exit this code
if number_processes('sftp-sync.py') == 1:

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-1]
    MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

    # get the sftp configuration information
    SFTP_INFO = wxcutils.load_json(CONFIG_PATH, 'sftp-sync.json')

    MY_LOGGER.debug('SFTP Server Info')
    hostname = SFTP_INFO['sftp site']
    MY_LOGGER.debug('sftp site = %s', hostname)
    Port = int(SFTP_INFO['port'])
    MY_LOGGER.debug('port = %s', Port)
    username = SFTP_INFO['username']
    MY_LOGGER.debug('username = %s', username)
    password = SFTP_INFO['password']
    MY_LOGGER.debug('password = -not logged-')
    MAX_AGE = SFTP_INFO['max_age'] * 60 * 60
    MY_LOGGER.debug('MAX_AGE = %s (seconds)', MAX_AGE)

    MY_LOGGER.debug('host keys')
    hostkeytype = None
    hostkey = None
    try:
        host_keys = paramiko.util.load_host_keys(
            os.path.expanduser('~/.ssh/known_hosts')
        )
    except IOError:
        MY_LOGGER.debug('*** Unable to open host keys file')
        host_keys = {}

    MY_LOGGER.debug('host key available?')
    if hostname in host_keys:
        hostkeytype = host_keys[hostname].keys()[0]
        hostkey = host_keys[hostname][hostkeytype]
        MY_LOGGER.debug('Using host key of type %s', hostkeytype)

    MY_LOGGER.debug('make connection')
    try:
        transport = paramiko.Transport((hostname, Port))
        transport.connect(hostkey, username, password, gss_host=socket.getfqdn(hostname))
        MY_LOGGER.debug('start sftp')
        sftp = paramiko.SFTPClient.from_transport(transport)

        # change directory on remote host
        MY_LOGGER.debug('change directory')
        sftp.chdir(SFTP_INFO['init_dir'])

        # sync remote to local
        remote_to_local('Meteor')

        # sync local to remote
        local_to_remote('Meteor')
        
        # close connection
        MY_LOGGER.debug('Closing client connection sftp')
        sftp.close()
        MY_LOGGER.debug('Closing client connection transport')
        transport.close()

    except Exception as e:
        print("*** Caught exception: %s: %s" % (e.__class__, e))
        traceback.print_exc()
        try:
            transport.close()
        except:
            pass
        sys.exit(1)

else:
    MY_LOGGER.debug('Another instance of sftp-sync.py is already running')
    MY_LOGGER.debug('Skip running this instance to allow the existing one to complete')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
