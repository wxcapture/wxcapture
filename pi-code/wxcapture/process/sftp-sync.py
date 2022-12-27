#!/usr/bin/env python3
"""sync meteor and noaa satellite data"""


# import libraries
import os
import sys
import subprocess
import sys
import os
import socket
import sys
import traceback
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


def remote_to_local(dir_name):
    """remote to local sync"""

    MY_LOGGER.debug('Syncing %s/Outbound remote to local', dir_name)

    # list files on the remote host
    MY_LOGGER.debug('get file list')
    file_listing = sftp.listdir(dir_name + '/Outbound')
    MY_LOGGER.debug('file_listing = %s', file_listing)

    # look for .wav files that:
    # start with the upper case of the directory name
    # end with .wav
    for entry in file_listing:
        if entry[-4:] == '.wav' and entry[:len(dir_name)] == dir_name.upper():
            # see if file already exists in AUDIO_PATH
            if not os.path.exists(AUDIO_PATH + entry):
                MY_LOGGER.debug('File %s does not yet exist - syncing', entry)
                # get file
                sftp.get(dir_name + '/Outbound/' + entry, AUDIO_PATH + entry)

                # need to kick off processing images based on .wav file and appropriate tle file

                # meteor
                # * run meteordemod
                # * re-run last locally received

                # NOAA
                # TBC!!!


def local_to_remote(dir_name):
    """local to remote sync"""

    MY_LOGGER.debug('Syncing local to remote %s/Inbound', dir_name)

    # list files on the remote host
    MY_LOGGER.debug('get remote file list')
    remote_file_listing = sftp.listdir(dir_name + '/Inbound')
    MY_LOGGER.debug('remote_file_listing = %s', remote_file_listing)

    # list local %composite.jpg (Meteor) or NOAA towards end of NOAA image files
    local_file_listing = os.listdir(IMAGE_PATH)
    MY_LOGGER.debug('local_file_listing = %s', local_file_listing)

    # copy %composite..jpg files over if not already on remote
    for local_file in local_file_listing:
        if dir_name.upper() in local_file and local_file not in remote_file_listing and ((local_file[-13:] == 'composite.jpg' and dir_name == 'Meteor') or (local_file[len(local_file) - 11 : len(local_file) - 7] == 'NOAA' and dir_name == 'NOAA')):
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
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# detailed paramiko logging
# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

# check if web is already running, if so exit this code
if number_processes('sftp-sync.py') == 1:

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-1]
    MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

    # get the configuration information
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'sftp-sync.json')

    MY_LOGGER.debug('SFTP Server Info')
    hostname = CONFIG_INFO['sftp site']
    MY_LOGGER.debug('sftp site = %s', hostname)
    Port = int(CONFIG_INFO['port'])
    MY_LOGGER.debug('port = %s', Port)
    username = CONFIG_INFO['username']
    MY_LOGGER.debug('username = %s', username)
    password = CONFIG_INFO['password']
    MY_LOGGER.debug('password = -not logged-')

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
        sftp.chdir(CONFIG_INFO['init_dir'])

        # sync remote to local
        remote_to_local('Meteor')
        remote_to_local('NOAA')

        # sync local to remote
        local_to_remote('Meteor')
        local_to_remote('NOAA')

        # close connection
        MY_LOGGER.debug('Closing client connection sftp')
        sftp.close()
        MY_LOGGER.debug('Closing client connection t')
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
