#!/usr/bin/env python3
"""Check that images are being created"""


# import libraries
import os
import time
import subprocess
import smtplib
import platform
import ssl
from subprocess import Popen, PIPE
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
    vf_data = ''

    # see when last modified
    last_modified = os.path.getmtime(WEB_PATH + vf_si['Location'] + '/' + vf_si['Test Image'])
    MY_LOGGER.debug('Last modified = %d', round(last_modified, 0))

    file_age = CURRENT_TIME - last_modified
    MY_LOGGER.debug('file_age = %d sec (Rounded [%s min] or [%s hours])', round(file_age,0), str(round(file_age / 60, 0)), str(round(file_age / 3600, 0)))

    vf_age_text = str(round(file_age / 60))
    vf_margin_text = str(round((file_age / 60) - float(vf_si['Max Age'])))

    # see if too old
    if file_age > (float(vf_si['Max Age']) * 60):
        MY_LOGGER.debug('Too old!')
        vf_text = 'ERROR ' + vf_si['Display Name'] + ' has exceeded the receiving threshold (' + \
            vf_si['Max Age'] + ' min) with age of ' + vf_age_text + \
            ' min - safety margin ' + vf_margin_text + ' min' + \
            NEWLINE
        vf_html = '<td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'
        vf_status = 'bad'
    else:
        MY_LOGGER.debug('Young enough')
        vf_text = 'OK    ' + vf_si['Display Name'] + ' is within the receiving threshold (' + \
            vf_si['Max Age'] + ' min) with age of ' + vf_age_text + \
            ' min - safety margin ' + vf_margin_text + ' min' + \
            NEWLINE
        vf_html = '<td style=\"background-color:#00FF00\" align=\"center\">OK</td>'

    if vf_status != vf_si['Last Status']:
        vf_change = 'Y'
    else:
        vf_change = 'N'

    vf_html = '<tr>' + vf_html + \
        '<td align=\"center\">' + vf_change + '</td>' + \
        '<td>' + vf_si['Display Name'] + '</td>' + \
        '<td align=\"center\">' + vf_si['Max Age'] + '</td>' + \
        '<td align=\"center\">' + vf_age_text + '</td>' + \
        '<td align=\"center\">' + vf_margin_text + '</td></tr>' + NEWLINE

    vf_data = vf_si['Display Name'] + ',' + str(CURRENT_TIME) + ',' + ALERT_INFO + ',' + vf_si['Max Age'] + ',' + vf_age_text + ',' + vf_margin_text + ',' + vf_change + ',' + vf_status + '\r\n'

    return vf_status, vf_text, vf_html, vf_data


def validate_server(vs_si):
    """validate server space used"""
    MY_LOGGER.debug('vs_si = %s',vs_si)

    vs_status = 'good'
    vs_text = ''
    vs_html = ''
    vs_data = ''

    # get the space used info from the file
    vs_space_used = wxcutils.load_file(vs_si['Location'], vs_si['File'])
    MY_LOGGER.debug('Space used = %s', vs_space_used)

    # see if too much used
    if int(vs_space_used) >= int(vs_si['Max Used']):
        MY_LOGGER.debug('Too much! %s >= %s', vs_space_used, vs_si['Max Used'])
        vs_text = 'ERROR ' + vs_si['Display Name'] + ' has exceeded the max percent used threshold (' + \
            vs_si['Max Used'] + ' percent) with ' + vs_space_used + ' percent used'
        vs_html = '<td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'
        vs_status = 'bad'
    else:
        MY_LOGGER.debug('Not too much %s < %s', vs_space_used, vs_si['Max Used'])
        vs_text = 'OK    ' + vs_si['Display Name'] + ' is within the max percent used threshold (' + \
            vs_si['Max Used'] + ' percent) with ' + vs_space_used + ' percent used'
        vs_html = '<td style=\"background-color:#00FF00\" align=\"center\">OK</td>'

    if vs_status != vs_si['Last Status']:
        vs_change = 'Y'
    else:
        vs_change = 'N'

    vs_margin = str(int(vs_si['Max Used']) - int(vs_space_used))
    vs_html = '<tr>' + vs_html + \
        '<td align=\"center\">' + vs_change + '</td>' + \
        '<td>' + vs_si['Display Name'] + '</td>' + \
        '<td align=\"center\">' + vs_si['Max Used'] + '</td>' + \
        '<td align=\"center\">' + vs_space_used + '</td>' + \
        '<td align=\"center\">' + vs_margin + '</td></tr>' + NEWLINE

    vs_data = vs_si['Display Name'] + ',' + str(CURRENT_TIME) + ',' + ALERT_INFO + ',' + vs_si['Max Used'] + ',' + vs_space_used + ',' + vs_margin + ',' + vs_change + ',' + vs_status + '\r\n'

    return vs_status, vs_text, vs_html, vs_data


def send_email(se_text, se_html, se_text2, se_html2):
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
    se_text = 'Status change - ' + ALERT_INFO + NEWLINE + \
        se_text + NEWLINE + \
        se_text2 + NEWLINE + \
        'Last status change on ' + ALERT_INFO 
    MY_LOGGER.debug('se_text = %s', se_text)

    # html text
    se_html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
        '<html><head>' + \
        '<title>Watchdog - Status Change</title></head>' + NEWLINE + \
        '<body><h2>' + 'Status Change - ' + ALERT_INFO + '</h2>' + NEWLINE + \
        '<h3>Satellites</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
        se_html + \
        '</table>' + NEWLINE + \
        '<h3>Servers</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Server</th><th>Max Used (percent)</th><th>Used (percent)</th><th>Delta (percent)</th></tr>' + \
        se_html2 + \
        '</table>' + NEWLINE +\
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
            dv_space = dv_line.split()[4].split('%')[0]
    MY_LOGGER.debug('dv_space  = %s used on %s', dv_space, platform.node())
    wxcutils.save_file(WORKING_PATH, 'used-' + platform.node() + '.txt', dv_space)


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def write_data():
    """write data to csv files"""

    # output data - sats
    MY_LOGGER.debug('Writing file update for sats - %s%s', OUTPUT_PATH, CSV_FILENAME)
    with open(OUTPUT_PATH + CSV_FILENAME, 'a+') as csv_file:
        if os.stat(OUTPUT_PATH + CSV_FILENAME).st_size == 0:
            csv_file.write('Satellite,Epoch Time (sec),Date,Max Age (min),Current Age (min),Margin Age (min),Status Change?,Status\r\n')
        csv_file.write(CSV_DATA)
        csv_file.close()

    # output data - servers
    MY_LOGGER.debug('Writing file update for servers - %s%s', OUTPUT_PATH, CSV_FILENAME2)
    with open(OUTPUT_PATH + CSV_FILENAME2, 'a+') as csv_file:
        if os.stat(OUTPUT_PATH + CSV_FILENAME2).st_size == 0:
            csv_file.write('Server,Epoch Time (sec),Date,Max Used (percent),Used (percent),Margin (percent),Status Change?,Status\r\n')
        csv_file.write(CSV_DATA2)
        csv_file.close()


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

CSV_FILENAME = 'satstatus.csv'
MY_LOGGER.debug('CSV_FILENAME = %s', CSV_FILENAME)
CSV_FILENAME2 = 'serverstatus.csv'
MY_LOGGER.debug('CSV_FILENAMEs = %s', CSV_FILENAME2)

# get current epoch time
CURRENT_TIME = time.time()
MY_LOGGER.debug('CURRENT_TIME = %d', CURRENT_TIME)

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]
MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

# email and data control info
STATUS_CHANGE_DETECTED = False
EMAIL_REQUIRED = False
EMAIL_TEXT = ''
EMAIL_HTML = ''
EMAIL_TEXT2 = ''
EMAIL_HTML2 = ''
CSV_DATA = ''
CSV_DATA2 = ''
NEWLINE = os.linesep + os.linesep

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
        status, text, html, data = validate_file(si)
        if status != si['Last Status']:
            STATUS_CHANGE_DETECTED = True
            EMAIL_REQUIRED = True
            MY_LOGGER.debug('Status change detected - old = %s, new = %s', si['Last Status'], status)
            si['Last Status'] = status
            si['Status Change'] = ALERT_INFO
        EMAIL_TEXT += text
        EMAIL_HTML += html
        CSV_DATA += data
    else:
        MY_LOGGER.debug('Satellite is not active')

MY_LOGGER.debug('-' * 20)


# validate space left on servers
SERVER_INFO = wxcutils.load_json(CONFIG_PATH, 'config-watchdog-servers.json')
MY_LOGGER.debug('current SERVER_INFO = %s', SERVER_INFO)

# create file for this server
drive_validation()

# iterate through servers
MY_LOGGER.debug('-' * 20)
MY_LOGGER.debug('Iterate through servers')
for si in SERVER_INFO:
    MY_LOGGER.debug('-' * 20)
    MY_LOGGER.debug('Processing - %s', si['Display Name'])
    if si['Active'] == 'yes':
        MY_LOGGER.debug('Active - Validation processing')
        # do the validation
        status, text, html, data = validate_server(si)
        if status != si['Last Status']:
            STATUS_CHANGE_DETECTED = True
            EMAIL_REQUIRED = True
            MY_LOGGER.debug('Status change detected - old = %s, new = %s', si['Last Status'], status)
            si['Last Status'] = status
            si['Status Change'] = ALERT_INFO
        EMAIL_TEXT2 += text
        EMAIL_HTML2 += html
        CSV_DATA2 += data
    else:
        MY_LOGGER.debug('Server is not active')

MY_LOGGER.debug('-' * 20)


# write data to the csv files
write_data()

MY_LOGGER.debug('-' * 20)
if EMAIL_REQUIRED:
    MY_LOGGER.debug('Email required...')

    MY_LOGGER.debug('Saving updated config')
    MY_LOGGER.debug('Sending Email')
    send_email(EMAIL_TEXT, EMAIL_HTML, EMAIL_TEXT2, EMAIL_HTML2)

    # save the new sat info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog.json', SATELLITE_INFO) 
    # save the new server info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog-servers.json', SERVER_INFO) 
    
else:
    MY_LOGGER.debug('No status changes so email not required...')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
