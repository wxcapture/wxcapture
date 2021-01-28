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


def validate_file(vs_name, vs_path, vs_file, vs_interval):
    """see if an image was created in a suitable
    time period"""
    MY_LOGGER.debug('vs_name = %s, vs_path = %s, vs_file = %s, vs_interval = %d',
                    vs_name, vs_path, vs_file, vs_interval)

    vf_status = True
    vf_text = ''
    vf_html = ''

    # see when last modified
    last_modified = os.path.getmtime(vs_path + vs_file)
    MY_LOGGER.debug('Last modified = %f', last_modified)

    file_age = CURRENT_TIME - last_modified
    MY_LOGGER.debug('file_age = %f sec (Rounded [%s min] or [%s hours])', file_age, str(round(file_age / 60)), str(round(file_age / 3600)))

    # see if too old
    if file_age > (vs_interval * 60):
        MY_LOGGER.debug('Too old!')
        vf_text = 'ERROR ' + vs_name + ' has exceeded the receiving threshold (' + \
            str(vs_interval) + ' min) with age of ' + str(round(file_age / 60)) + \
            ' min - delta ' + str(round((file_age / 60) - vs_interval)) + ' min' + \
            os.linesep + os.linesep
        vf_html = '<td style=\"background-color:#FF0000\">ERROR</td>'
        vf_status = False
    else:
        MY_LOGGER.debug('Young enough')
        vf_text = 'OK    ' + vs_name + ' is within the receiving threshold (' + \
            str(vs_interval) + ' min) with age of ' + str(round(file_age / 60)) + \
            ' min - delta ' + str(round((file_age / 60) - vs_interval)) + ' min' + \
            os.linesep + os.linesep
        vf_html = '<td style=\"background-color:#00FF00\">OK</td>'

    vf_html = '<tr>' + vf_html + '<td>' + vs_name + '</td>' + \
        '<td>' + str(vs_interval) + '</td>' + \
        '<td>' + str(round(file_age / 60)) + '</td>' + \
        '<td>' + str(round((file_age / 60) - vs_interval)) + '</td></tr>'

    return vf_status, vf_text, vf_html


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

# load email config
EMAIL_INFO = wxcutils.load_json(CONFIG_PATH, 'email.json')

# load status of last run
STATUS_INFO = wxcutils.load_json(CONFIG_PATH, 'email_status.json')
MY_LOGGER.debug('Status of last run = %s', STATUS_INFO['last status'])
MY_LOGGER.debug('Date of last change = %s', STATUS_INFO['status change'])

# email info
ISSUE_DETECTED = False
EMAIL_TEXT = ''
EMAIL_HTML = ''

# validate each satellite with an example image which is frequently
# received and processed at a frequency ~ twice the expected frequency in minutes

# Geostationary
# GK-2A - 30 min
ok, text, html = validate_file('GK-2A', '/home/websites/wxcapture/gk-2a/', 'FD.jpg', 30)
if not ok:
    ISSUE_DETECTED = True
EMAIL_TEXT += text
EMAIL_HTML += html

# GOES 17 - 120 min
ok, text, html = validate_file('GOES 17', '/home/websites/wxcapture/goes/', 'goes_17_fd_fc.jpg', 120)
if not ok:
    ISSUE_DETECTED = True
EMAIL_TEXT += text
EMAIL_HTML += html

# GOES 16 - 120 min
ok, text, html = validate_file('GOES 16', '/home/websites/wxcapture/goes/', 'goes_16_fd_ch13.jpg', 120)
if not ok:
    ISSUE_DETECTED = True
EMAIL_TEXT += text
EMAIL_HTML += html

# Himawari 8 - 120 min
ok, text, html = validate_file('Himawari 8', '/home/websites/wxcapture/goes/', 'himawari_8_fd_IR.jpg', 120)
if not ok:
    ISSUE_DETECTED = True
EMAIL_TEXT += text
EMAIL_HTML += html

# Polar
# Predictions - 25 hours
ok, text, html = validate_file('Polar orbiting predictions', '/home/websites/wxcapture/', 'satpass.html', 25 * 60)
if not ok:
    ISSUE_DETECTED = True
EMAIL_TEXT += text
EMAIL_HTML += html

# Passes - 12 hours
ok, text, html = validate_file('Polar passes', '/home/websites/wxcapture/', 'polar.txt', 12 * 60)
if not ok:
    ISSUE_DETECTED = True
EMAIL_TEXT += text
EMAIL_HTML += html


# send email if required
# this is where the status has changed
# from good to bad (or back agai)
if (ISSUE_DETECTED and STATUS_INFO['last status'] == 'good') or (not ISSUE_DETECTED and STATUS_INFO['last status'] == 'bad'):
    # add additional info to the email
    ALERT_INFO = get_local_date_time() + ' ' +  LOCAL_TIME_ZONE + \
        ' [' + get_utc_date_time() + ' UTC].'

    if ISSUE_DETECTED:
        ALERT_TEXT = 'Issue detected'
    else:
        ALERT_TEXT = 'Issue resolved'

    MY_LOGGER.debug('sending email')

    # setup the message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Watchdog - " + ALERT_TEXT
    message["From"] = EMAIL_INFO['from']
    message["To"] = EMAIL_INFO['notify']
    MY_LOGGER.debug('Sending (header) to = %s', EMAIL_INFO['notify'])
    MY_LOGGER.debug('Sending (deliver) to:') 
    for email_address in EMAIL_INFO['notify'].split(','):
        MY_LOGGER.debug('* ' + email_address)

    # plain text
    EMAIL_TEXT = ALERT_TEXT + ' - ' + ALERT_INFO + os.linesep + os.linesep + \
        EMAIL_TEXT + os.linesep + os.linesep + \
        'Last status change on ' + ALERT_INFO
    MY_LOGGER.debug('EMAIL_TEXT = %s', EMAIL_TEXT)

    # html text
    EMAIL_HTML = '<html><body><h2>' + ALERT_TEXT + ' - ' + ALERT_INFO + '</h2>' + \
        '<table border=1>' + \
        '<tr><th>Status</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
         EMAIL_HTML + \
        '</table>' + \
        '<p>Last status change on ' + ALERT_INFO + '</p>' + \
        '</body></html>'
    MY_LOGGER.debug('EMAIL_HTML = %s', EMAIL_HTML)

    # build email
    message.attach(MIMEText(EMAIL_TEXT, "plain"))
    message.attach(MIMEText(EMAIL_HTML, "html"))

    # send email
    context = ssl.create_default_context()
    with smtplib.SMTP(EMAIL_INFO['smtp server'], EMAIL_INFO['smtp server port']) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(EMAIL_INFO['username'], EMAIL_INFO['password'])
        server.sendmail(EMAIL_INFO['from'], EMAIL_INFO['notify'].split(','), message.as_string())

    # update status file
    MY_LOGGER.debug('updating changed status')
    if ISSUE_DETECTED:
        STATUS_INFO['last status'] = 'bad'
    else:
        STATUS_INFO['last status'] = 'good'
    STATUS_INFO['status change'] = ALERT_INFO
    wxcutils.save_json(CONFIG_PATH, 'email_status.json', STATUS_INFO)

else:
    MY_LOGGER.debug('Status unchanged - not sending email')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
