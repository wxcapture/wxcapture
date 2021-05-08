#!/usr/bin/env python3
"""Check that the email server is working"""


# import libraries
import os
import time
import smtplib
import platform
import ssl
import sys
import subprocess
from subprocess import Popen, PIPE
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import wxcutils


def send_email(se_config_file, se_subject):
    """send the email"""

    se_ok_status = True
    MY_LOGGER.debug('Using config file %s', se_config_file)

    # load email config
    email_info = wxcutils.load_json(CONFIG_PATH, se_config_file)
    # don't log ALL the email config, it includes a password

    # setup the message
    message = MIMEMultipart('alternative')
    message['Subject'] = se_subject
    message['From'] = email_info['from']
    message['To'] = email_info['notify']
    MY_LOGGER.debug('Sending (header) to = %s', email_info['notify'])
    MY_LOGGER.debug('Sending (deliver) to:')
    for email_address in email_info['notify'].split(','):
        MY_LOGGER.debug('EMAIL TO -----> %s', email_address)

    # plain text
    se_text = se_subject + ALERT_INFO + NEWLINE
    MY_LOGGER.debug('se_text = %s', se_text)

    # html text
    se_html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
        '<html><head>' + \
        '<title>' + se_subject + '</title></head>' + NEWLINE + \
        '<body><h2>' + se_subject + ' - ' + ALERT_INFO + '</h2>' + NEWLINE + \
        '</body></html>'
    MY_LOGGER.debug('se_html = %s', se_html)

    # build email
    message.attach(MIMEText(se_text, "plain"))
    message.attach(MIMEText(se_html, "html"))

    # send email
    try:
        MY_LOGGER.debug('Trying to send email')
        context = ssl.create_default_context()
        with smtplib.SMTP(email_info['smtp server'], email_info['smtp server port']) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(email_info['username'], email_info['password'])
            server.sendmail(email_info['from'], email_info['notify'].split(','),
                            message.as_string())
            MY_LOGGER.debug('Email sent')
    except:
        se_ok_status = False
        MY_LOGGER.error('Email sending error - %s %s %s', sys.exc_info()[0],
                        sys.exc_info()[1], sys.exc_info()[2])

    return se_ok_status


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'web/'
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

# get current epoch time
CURRENT_TIME = time.time()
MY_LOGGER.debug('CURRENT_TIME = %d', CURRENT_TIME)

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]
MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

# newline definition
NEWLINE = os.linesep + os.linesep

# get the run time, to use for email date time
ALERT_INFO = get_local_date_time() + ' ' +  LOCAL_TIME_ZONE + \
        ' [' + get_utc_date_time() + ' UTC].'
MY_LOGGER.debug('ALERT_INFO = %s', ALERT_INFO)

MY_LOGGER.debug('-' * 20)
# try to send email to main server
MY_LOGGER.debug('Trying main email server')
if not send_email('email.json', 'Main server test'):
    MY_LOGGER.error('Error with main server, restart postfix and dovecot')
    MY_LOGGER.debug('Restart postfix')
    wxcutils.run_cmd('postfix stop')
    wxcutils.run_cmd('postfix start')
    MY_LOGGER.debug('Restart dovecot')
    wxcutils.run_cmd('systemctl stop dovecot')
    wxcutils.run_cmd('systemctl start dovecot')
    MY_LOGGER.debug('Sleeping 10 sec to allow servers to restart')
    time.sleep(10)
    MY_LOGGER.debug('Trying main email server post restarts')
    if not send_email('email.json', 'Main server test'):
        MY_LOGGER.error('Error with main server, need to reboot')
        # notify issue via alternate email server
        if not send_email('email2.json', 'Alternate server email - main server REBOOT'):
            MY_LOGGER.debug('Sending Email using alternate server also failed')
        else:
            MY_LOGGER.debug('Sending Email using alternate server worked')
        MY_LOGGER.debug('Rebooting server')
        wxcutils.run_cmd('reboot')
else:
    MY_LOGGER.debug('Main email server working fine')

MY_LOGGER.debug('-' * 20)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
