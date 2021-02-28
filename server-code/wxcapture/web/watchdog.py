#!/usr/bin/env python3
"""Check that images are being created"""


# import libraries
import os
import time
import subprocess
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import wxcutils


def validate_file(vf_si):
    """see if an image was created in a suitable
    time period"""
    MY_LOGGER.debug('vf_si = %s',vf_si)

    vf_status = 'good'
    vf_text = ''
    vf_html = ''

    # see when last modified
    last_modified = os.path.getmtime(WEB_PATH + vf_si['Location'] + '/' + vf_si['Test Image'])
    MY_LOGGER.debug('Last modified = %d', round(last_modified, 0))

    file_age = CURRENT_TIME - last_modified
    MY_LOGGER.debug('file_age = %d sec (Rounded [%s min] or [%s hours])', round(file_age,0), str(round(file_age / 60, 0)), str(round(file_age / 3600, 0)))

    # see if too old
    if file_age > (float(vf_si['Max Age']) * 60):
        MY_LOGGER.debug('Too old!')
        vf_text = 'ERROR ' + vf_si['Display Name'] + ' has exceeded the receiving threshold (' + \
            vf_si['Max Age'] + ' min) with age of ' + str(round(file_age / 60)) + \
            ' min - safety margin ' + str(round((file_age / 60) - float(vf_si['Max Age']))) + ' min' + \
            os.linesep + os.linesep
        vf_html = '<td style=\"background-color:#FF0000\">ERROR</td>'
        vf_status = 'bad'
    else:
        MY_LOGGER.debug('Young enough')
        vf_text = 'OK    ' + vf_si['Display Name'] + ' is within the receiving threshold (' + \
            vf_si['Max Age'] + ' min) with age of ' + str(round(file_age / 60)) + \
            ' min - safety margin ' + str(round((file_age / 60) - float(vf_si['Max Age']))) + ' min' + \
            os.linesep + os.linesep
        vf_html = '<td style=\"background-color:#00FF00\">OK</td>'

    vf_html = '<tr>' + vf_html + '<td>' + vf_si['Display Name'] + '</td>' + \
        '<td>' + vf_si['Max Age'] + '</td>' + \
        '<td>' + str(round(file_age / 60)) + '</td>' + \
        '<td>' + str(round((file_age / 60) - float(vf_si['Max Age']))) + '</td></tr>'

    return vf_status, vf_text, vf_html


def send_email(se_text, se_html):
    """send the email"""

    # load email config
    EMAIL_INFO = wxcutils.load_json(CONFIG_PATH, 'email.json')
    # don't log ALL the email config, it includes a password

    # setup the message
    message = MIMEMultipart('alternative')
    message['Subject'] = 'Watchdog - Status Change'
    message['From'] = EMAIL_INFO['from']
    message['To'] = EMAIL_INFO['notify']
    MY_LOGGER.debug('Sending (header) to = %s', EMAIL_INFO['notify'])
    MY_LOGGER.debug('Sending (deliver) to:') 
    for email_address in EMAIL_INFO['notify'].split(','):
        MY_LOGGER.debug('EMAIL TO -----> ' + email_address)

    # plain text
    se_text = 'Status change - ' + ALERT_INFO + os.linesep + os.linesep + \
        se_text + os.linesep + os.linesep + \
        'Last status change on ' + ALERT_INFO
    MY_LOGGER.debug('se_text = %s', se_text)

    # html text
    se_html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
        '<html><head>' + \
        '<title>Watchdog - Status Change</title></head>' + \
        '<body><h2>' + 'Status Change - ' + ALERT_INFO + '</h2>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
        se_html + \
        '</table>' + \
        '<p>Last status change on ' + ALERT_INFO + '</p>' + \
        '</body></html>'
    MY_LOGGER.debug('se_html = %s', se_html)

    # build email
    message.attach(MIMEText(se_text, "plain"))
    message.attach(MIMEText(se_html, "html"))

    # send email
    context = ssl.create_default_context()
    with smtplib.SMTP(EMAIL_INFO['smtp server'], EMAIL_INFO['smtp server port']) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(EMAIL_INFO['username'], EMAIL_INFO['password'])
        server.sendmail(EMAIL_INFO['from'], EMAIL_INFO['notify'].split(','), message.as_string())


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

WEB_PATH = '/home/websites/wxcapture/'
MY_LOGGER.debug('WEB_PATH = %s', WEB_PATH)

# get current epoch time
CURRENT_TIME = time.time()
MY_LOGGER.debug('CURRENT_TIME = %d', CURRENT_TIME)

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]
MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

# email control info
STATUS_CHANGE_DETECTED = False
EMAIL_REQUIRED = False
EMAIL_TEXT = ''
EMAIL_HTML = ''

# load satellite info
SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'config-watchdog.json')
# MY_LOGGER.debug('current SATELLITE_INFO = %s', SATELLITE_INFO)

# get the run time, to use for status update date time
ALERT_INFO = get_local_date_time() + ' ' +  LOCAL_TIME_ZONE + \
        ' [' + get_utc_date_time() + ' UTC].'
MY_LOGGER.debug('ALERT_INFO = %s', ALERT_INFO)

# iterate through satellites
MY_LOGGER.debug('-' * 20)
MY_LOGGER.debug('Iterate through satellites')
for si in SATELLITE_INFO:
    MY_LOGGER.debug('-' * 20)
    MY_LOGGER.debug('Processing - %s', si['Display Name'])
    if si['Active'] == 'yes':
        MY_LOGGER.debug('Active - Validation processing')
        # do the validation
        status, text, html = validate_file(si)
        if status != si['Last Status']:
            STATUS_CHANGE_DETECTED = True
            EMAIL_REQUIRED = True
            MY_LOGGER.debug('Status change detected - old = %s, new = %s', si['Last Status'], status)
            si['Last Status'] = status
            si['Status Change'] = ALERT_INFO
        EMAIL_TEXT += text
        EMAIL_HTML += html
    else:
        MY_LOGGER.debug('Satellite is not active')

MY_LOGGER.debug('-' * 20)

if EMAIL_REQUIRED:
    MY_LOGGER.debug('Email required...')

    MY_LOGGER.debug('Saving updated config')
    MY_LOGGER.debug('Sending Email')
    send_email(EMAIL_TEXT, EMAIL_HTML)

    # save the new sat info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog.json', SATELLITE_INFO) 
else:
    MY_LOGGER.debug('No status changes so email not required...')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
