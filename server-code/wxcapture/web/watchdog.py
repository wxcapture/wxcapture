#!/usr/bin/env python3
"""Check that images are being created"""


# import libraries
import os
import time
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

    # see when last modified
    last_modified = os.path.getmtime(vs_path + vs_file)
    MY_LOGGER.debug('Last modified = %f', last_modified)

    file_age = CURRENT_TIME - last_modified
    MY_LOGGER.debug('file_age = %f sec (Rounded [%s min] or [%s hours])', file_age, str(round(file_age / 60)), str(round(file_age / 3600)))

    # see if too old
    if file_age > vs_interval:
        MY_LOGGER.debug('Too old!')
        return False, vs_name + ' has exceeded the receiving threshold (' + str(round(vs_interval / 60)) + ' min) with age of ' + str(round(file_age / 60)) + ' min' + os.linesep + os.linesep
    MY_LOGGER.debug('Young enough')
    return True, ''


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

# load email config
EMAIL_INFO = wxcutils.load_json(CONFIG_PATH, 'email.json')

# email info
EMAIL_REQUIRED = False
EMAIL_TEXT_SAT = ''

# validate each satellite with an example image which is frequently
# received and processed at a frequency ~ twice the expected frequency in seconds

# Geostationary
# GK-2A - 30 min
ok, text = validate_file('GK-2A', '/home/websites/wxcapture/gk-2a/', 'FD.jpg', 30 * 60)
if not ok:
    EMAIL_REQUIRED = True
    EMAIL_TEXT_SAT += text

# GOES 17 - 120 min
ok, text = validate_file('GOES 17', '/home/websites/wxcapture/goes/', 'goes_17_fd_fc.jpg', 120 * 60)
if not ok:
    EMAIL_REQUIRED = True
    EMAIL_TEXT_SAT += text

# GOES 16 - 120 min
ok, text = validate_file('GOES 16', '/home/websites/wxcapture/goes/', 'goes_16_fd_ch13.jpg', 120 * 60)
if not ok:
    EMAIL_REQUIRED = True
    EMAIL_TEXT_SAT += text

# Himawari 8 - 120 min
ok, text = validate_file('Himawari 8', '/home/websites/wxcapture/goes/', 'himawari_8_fd_IR.jpg', 120 * 60)
if not ok:
    EMAIL_REQUIRED = True
    EMAIL_TEXT_SAT += text


# Polar
# Predictions - 25 hours
ok, text = validate_file('Polar orbiting predictions', '/home/websites/wxcapture/', 'satpass.html', 25 * 60 * 60)
if not ok:
    EMAIL_REQUIRED = True
    EMAIL_TEXT_SAT += text

# Passes - 12 hours
ok, text = validate_file('Polar passes', '/home/websites/wxcapture/', 'polar.txt', 12 * 60 * 60)
if not ok:
    EMAIL_REQUIRED = True
    EMAIL_TEXT_SAT += text


# send email if required
if EMAIL_REQUIRED:
    MY_LOGGER.debug('sending email')
    MY_LOGGER.debug('EMAIL_TEXT_SAT = %s', EMAIL_TEXT_SAT)
    EMAIL_HTML_SAT = '<html><body><p>' + EMAIL_TEXT_SAT.replace(os.linesep, '<br>') + '</p></body></html>'

    # setup the message
    message = MIMEMultipart("alternative")
    message["Subject"] = "Watchdog Alert"
    message["From"] = EMAIL_INFO['from']
    message["To"] = EMAIL_INFO['notify']

    # build email
    message.attach(MIMEText(EMAIL_TEXT_SAT, "plain"))
    message.attach(MIMEText(EMAIL_HTML_SAT, "html"))

    # send email
    context = ssl.create_default_context()
    with smtplib.SMTP(EMAIL_INFO['smtp server'], EMAIL_INFO['smtp server port']) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(EMAIL_INFO['username'], EMAIL_INFO['password'])
        server.sendmail(EMAIL_INFO['from'], EMAIL_INFO['notify'], message.as_string())
else:
    MY_LOGGER.debug('No issues identified, no need to send email')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
