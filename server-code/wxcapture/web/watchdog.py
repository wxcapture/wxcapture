#!/usr/bin/env python3
"""Check that images are being created"""


# import libraries
import os
import time
import smtplib
import platform
import ssl
import sys
import subprocess
from subprocess import Popen, PIPE
from urllib.request import urlopen
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import wxcutils


def get_email_info():
    """get the initial email info"""

    # send status update on first run in a day
    # otherwise only send on a status change
    if (int(time.strftime('%H')) == 0) and (1 < int(time.strftime('%M')) < 14):
        MY_LOGGER.debug('Daily update email')
        return 'Daily Update', True
    MY_LOGGER.debug('Status change email')
    return 'Status Change', False


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def send_email(se_text, se_html, se_config_file):
    """send the email"""

    se_ok_status = True
    MY_LOGGER.debug('Using config file %s', se_config_file)

    # load email config
    email_info = wxcutils.load_json(CONFIG_PATH, se_config_file)
    # don't log ALL the email config, it includes a password

    # setup the message
    message = MIMEMultipart('alternative')
    message['Subject'] = 'Watchdog - ' + EMAIL_SUBJECT
    message['From'] = email_info['from']
    message['To'] = email_info['notify']
    MY_LOGGER.debug('Sending (header) to = %s', email_info['notify'])
    MY_LOGGER.debug('Sending (deliver) to:')
    for email_address in email_info['notify'].split(','):
        MY_LOGGER.debug('EMAIL TO -----> %s', email_address)

    # plain text
    se_email_text = EMAIL_SUBJECT + ' - ' + ALERT_INFO + NEWLINE + \
        se_text + NEWLINE + \
        'Last status change on ' + ALERT_INFO
    MY_LOGGER.debug('se_email_text = %s', se_email_text)

    # html text
    se_email_html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
        '<html><head>' + \
        '<title>Watchdog - ' + EMAIL_SUBJECT + '</title></head>' + NEWLINE + \
        '<body><h2>' + EMAIL_SUBJECT + ' - ' + ALERT_INFO + '</h2>' + NEWLINE + \
         se_html + NEWLINE + \
        '<p>Last status change on ' + ALERT_INFO + '</p>' + \
        '</body></html>'
    MY_LOGGER.debug('se_email_html = %s', se_email_html)

    # build email
    message.attach(MIMEText(se_email_text, "plain"))
    message.attach(MIMEText(se_email_html, "html"))

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


def validate_file(vf_si):
    """see if an image was created in a suitable
    time period"""
    MY_LOGGER.debug('vf_si = %s', vf_si)

    vf_status = 'good'
    vf_text = ''
    vf_html = ''

    # see when last modified
    last_modified = os.path.getmtime(WEB_PATH + vf_si['Location'] + '/' + vf_si['Test Image'])
    MY_LOGGER.debug('Last modified = %d', round(last_modified, 0))

    file_age = CURRENT_TIME - last_modified
    MY_LOGGER.debug('file_age = %d sec (Rounded [%s min] or [%s hours])', round(file_age, 0),
                    str(round(file_age / 60, 0)), str(round(file_age / 3600, 0)))

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

    # check if too old
    if int(vf_margin_text) >= MAX_AGE:
        MY_LOGGER.debug('max age reached, don''t report')
        vf_text = ''
        vf_html = ''
    else:
        MY_LOGGER.debug('less than max age, so report')

    return vf_status, vf_text, vf_html


def check_webserver_images():
    """check images on the webserver"""
    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('Iterate through satellites on this server')
    response_text = ''
    response_html = ''
    response_email_required = False

    for si in SATELLITE_INFO:
        MY_LOGGER.debug('-' * 10)
        MY_LOGGER.debug('Processing - %s', si['Display Name'])
        if si['Active'] == 'yes':
            MY_LOGGER.debug('Active - Validation processing')
            # do the validation
            status, text, html = validate_file(si)
            if status != si['Last Status']:
                response_email_required = True
                MY_LOGGER.debug('Status change detected - old = %s, new = %s',
                                si['Last Status'], status)
                si['Last Status'] = status
                si['Status Change'] = ALERT_INFO
            response_text += text
            response_html += html
        else:
            MY_LOGGER.debug('Satellite is not active')
    MY_LOGGER.debug('-' * 10)

    # add in HTML header / footer
    response_html = '<h3>Satellites - Web Server</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
        response_html + NEWLINE + \
        '</table>' + NEWLINE

    MY_LOGGER.debug('=' * 30)
    return response_text, response_html, response_email_required


def check_data_server_images():
    """check images on the data server"""
    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('Iterate through satellites on the data server')
    response_text = ''
    response_html = ''
    response_email_required = False

    for sd in SATELLITE_DATA:
        MY_LOGGER.debug('-' * 10)
        if sd['Active'] == 'yes':
            MY_LOGGER.debug('Satellite = %s', sd['Display Name'])
            if sd['Last Status'] == 'OK':
                msg = ' is within the receiving threshold ('
                sat_status = '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
                MY_LOGGER.debug('OK - within threshold')
            else:
                msg = ' has exceeded the receiving threshold ('
                sat_status = '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'
                MY_LOGGER.debug('ERROR - exceeded threshold')
            if sd['Current Age'] != 'n/a':
                margin = str(int(sd['Max Age']) - int(sd['Current Age']))
            else:
                margin = 'n/a'
            MY_LOGGER.debug('Margin = %a', margin)

            # check if too old
            MY_LOGGER.debug('margin = %s', margin)
            if margin == 'n/a':
                MY_LOGGER.debug('no images on server, don''t report')
            elif int(margin) <= (-1 * MAX_AGE):
                MY_LOGGER.debug('max age reached, don''t report')
            else:
                MY_LOGGER.debug('less than max age, so report')
                response_text += sd['Last Status'] + ' ' + sd['Display Name'] + msg + \
                    sd['Max Age'] + ' min) with age of ' + sd['Current Age'] + \
                    ' min - safety margin ' + margin + ' min' + \
                    NEWLINE
                response_html += sat_status + \
                    '<td align=\"center\">' + sd['Status Change'] + '</td>' +\
                    '<td align=\"center\">' + sd['Display Name'] + '</td>' +\
                    '<td align=\"center\">' + sd['Max Age'] + '</td>' +\
                    '<td align=\"center\">' + sd['Current Age'] + '</td>' +\
                    '<td align=\"center\">' + margin + '</td></tr>' + NEWLINE

        else:
            MY_LOGGER.debug('Skipping satellite = %s as inactive', sd['Display Name'])

    MY_LOGGER.debug('-' * 10)

    # add in HTML header / footer
    response_html = '<h3>Satellites - Data Server</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
        response_html + NEWLINE + \
        '</table>' + NEWLINE

    MY_LOGGER.debug('=' * 30)
    return response_text, response_html, response_email_required


def drive_validation():
    """validate drive space utilisation"""
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


def validate_server(vs_si):
    """validate server space used"""
    MY_LOGGER.debug('vs_si = %s', vs_si)

    vs_status = 'good'
    vs_text = ''
    vs_html = ''

    # get the space used info from the file
    vs_space_used = wxcutils.load_file(vs_si['Location'], vs_si['File'])
    MY_LOGGER.debug('Space used = %s', vs_space_used)

    # see if too much used
    if int(vs_space_used) >= int(vs_si['Max Used']):
        MY_LOGGER.debug('Too much! %s >= %s', vs_space_used, vs_si['Max Used'])
        vs_text = 'ERROR ' + vs_si['Display Name'] + \
            ' has exceeded the max percent used threshold (' + \
            vs_si['Max Used'] + ' percent) with ' + vs_space_used + ' percent used'
        vs_html = '<td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'
        vs_status = 'bad'
    else:
        MY_LOGGER.debug('Not too much %s < %s', vs_space_used, vs_si['Max Used'])
        vs_text = 'OK    ' + vs_si['Display Name'] + \
            ' is within the max percent used threshold (' + \
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

    return vs_status, vs_text, vs_html


def check_drive_space():
    """validate free space on each server"""

    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('validate free space on each server')
    response_text = ''
    response_html = ''
    response_email_required = False

    # create file for this server
    drive_validation()

    for si in SERVER_INFO:
        MY_LOGGER.debug('-' * 10)
        MY_LOGGER.debug('Processing - %s', si['Display Name'])
        if si['Active'] == 'yes':
            MY_LOGGER.debug('Active - Validation processing')
            # do the validation
            status, text, html = validate_server(si)
            if status != si['Last Status']:
                response_email_required = True
                MY_LOGGER.debug('Status change detected - old = %s, new = %s',
                                si['Last Status'], status)
                si['Last Status'] = status
                si['Status Change'] = ALERT_INFO
            response_text += text
            response_html += html + NEWLINE
        else:
            MY_LOGGER.debug('Server is not active')
    MY_LOGGER.debug('-' * 10)

    # add in HTML header / footer
    response_html = '<h3>Server Space</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Server</th><th>Max Used (percent)</th><th>Used (percent)</th><th>Delta (percent)</th></tr>' + \
        response_html + NEWLINE + \
        '</table>' + NEWLINE

    MY_LOGGER.debug('=' * 30)
    return response_text, response_html, response_email_required


def check_network():
    """validate network connectivity"""

    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('validate network connectivity')
    response_text = ''
    response_html = ''
    response_email_required = False

    for key, value in LATESTNETWORK.items():
        if key == 'addresses':
            for nc in LATESTNETWORK[key]:
                if nc['Active'] == 'yes':
                    MY_LOGGER.debug('-' * 10)
                    MY_LOGGER.debug(nc)
                    if nc['status'] == 'OK':
                        response_html += '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
                    else:
                        response_html += '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'

                    # get the previous state
                    for key2, value2 in PREVIOUSTNETWORK.items():
                        if key2 == 'addresses':
                            for nc2 in PREVIOUSTNETWORK[key]:
                                if nc['description'] == nc2['description']:
                                    PREVIOUS = nc2
                                    MY_LOGGER.debug('Previous = %s', PREVIOUS)

                    CHANGE = 'N'
                    if nc['status'] != PREVIOUS['status']:
                        response_email_required = True
                        CHANGE = 'Y'
                    response_html += '<td align = \"center\">' + CHANGE + '</td>'

                    response_text += nc['description'] + ' - '
                    response_html += '<td>' + nc['description'] + '</td>'

                    if nc['status'] == 'OK':
                        response_text += 'OK - network connectivity is good' + ' - '
                        response_html += '<td>Good connectivity</td></tr>' + NEWLINE
                    else:
                        response_text = 'Error - network connecitivity issue - ' + nc['status'] + ''
                        response_html += '<td>' + nc['status'] + '</td></tr>' + NEWLINE
    MY_LOGGER.debug('-' * 10)

    # add in HTML header / footer
    response_html = '<h3>Network Connectivity</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Connection</th><th>Information</th></tr>' + \
        response_html + NEWLINE + \
        '</table>' + NEWLINE

    MY_LOGGER.debug('=' * 30)
    return response_text, response_html, response_email_required


def check_sat_status():
    """validate satellite status"""

    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('validate satellite status')
    response_text = ''
    response_html = ''
    response_email_required = False

    for si1 in LATESTSATSTATUS:
        MY_LOGGER.debug('-' * 10)
        MY_LOGGER.debug('Processing - %s', si1['label'])
        MY_LOGGER.debug('si1 %s', si1)

        for si2 in PREVIOUSSATSTATUS:
            if si1['label'] == si2['label']:
                MY_LOGGER.debug('si2 %s', si2)
                if si1['ok'] == 'Locked':
                    response_html += '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
                else:
                    response_html += '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'

                CHANGE = 'N'
                if si1['ok'] != si2['ok']:
                    response_email_required = True
                    CHANGE = 'Y'
                response_html += '<td align = \"center\">' + CHANGE + '</td>'

                response_text += si1['label'] + ' - ' + si1['ok'] + ' - ' + \
                    str(si1['skipped_symbols']) + ' - ' + \
                    str(si1['reed_solomon_errors']) + ' - ' + str(si1['viterbi_errors']) + NEWLINE
                response_html += '<td>' +  si1['label'] + '</td><td>' + si1['ok'] + '</td><td align=\"center\">' + \
                    str(si1['skipped_symbols']) + \
                    '</td><td align=\"center\">' + str(si1['reed_solomon_errors']) + '</td><td align=\"center\">' + \
                    str(si1['viterbi_errors']) + '</td></tr>' + NEWLINE
    MY_LOGGER.debug('-' * 10)

    # add in HTML header / footer
    response_html = '<h3>Satellite Lock</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Connection</th><th>Lock?</th><th>Skipped Symbols</th><th>Reed Solomon Errors</th><th>Viterbi Errors</th></tr>' + \
        response_html + NEWLINE + \
        '</table>' + NEWLINE

    MY_LOGGER.debug('=' * 30)
    return response_text, response_html, response_email_required


def check_ip(address, attempts):
    """Check if IP address responds to pings"""
    cmd = Popen(['ping', address, '-c', str(attempts), '-W', '1']
                , stdout=PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    MY_LOGGER.debug('%s stdout = %s', address, stdout.decode('utf-8'))
    MY_LOGGER.debug('%s stderr = %s', address, stderr.decode('utf-8'))
    if '100% packet loss' in stdout.decode('utf-8'):
        return False
    if 'Destination Host Unreachable' in stdout.decode('utf-8'):
        return False
    if 'No route to host' in stdout.decode('utf-8'):
        return False
    return True


def check_pings():
    """validate pings"""

    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('validate pings')
    response_text = ''
    response_html = ''
    response_email_required = False

    MY_LOGGER.debug('Retries = %s', PINGS['retries'])
    MY_LOGGER.debug('Pause = %s', PINGS['pause'])
    MY_LOGGER.debug('Attempts = %s', PINGS['attempts'])

    for key, value in PINGS.items():
        if key == 'addresses':
            for ping in PINGS[key]:
                MY_LOGGER.debug('-' * 10)

                if ping['Active'] == 'yes':
                    MY_LOGGER.debug('Testing - %s', ping['description'])
                    new_status = 'ERROR'
                    loop = 0
                    while loop < int(PINGS['retries']):
                        if check_ip(ping['ip'], PINGS['attempts']):
                            new_status = 'OK'
                            break
                        loop += 1
                        MY_LOGGER.debug('Retry %d of %s', loop, PINGS['retries'])
                        MY_LOGGER.debug('Sleep %s seconds', PINGS['pause'])
                        time.sleep(int(PINGS['pause']))
                    MY_LOGGER.debug(ping)
                    MY_LOGGER.debug('new_status = %s', new_status)
                    if new_status == 'OK':
                        response_html += '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
                    else:
                        response_html += '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'

                    # get the previous state
                    MY_LOGGER.debug('Previous status = %s', ping['status'])
                    change = 'N'
                    if new_status != ping['status']:
                        response_email_required = True
                        change = 'Y'
                        ping['when'] = int(CURRENT_TIME)
                    response_html += '<td align = \"center\">' + change + '</td>'
                    ping['status'] = new_status

                    response_text += ping['description'] + ' - '
                    response_html += '<td>' + ping['description'] + '</td>'

                    margin = int((CURRENT_TIME - ping['when']) / 60)
                    MY_LOGGER.debug('margin = %d', margin)

                    if new_status == 'OK':
                        response_text += 'OK - network connectivity is good' + NEWLINE
                        response_html += '<td>Good connectivity</td></tr>' + NEWLINE
                    else:
                        response_text = 'Error - network connecitivity issue  is bad' + NEWLINE
                        response_html += '<td>Bad connectivity</td></tr>' + NEWLINE
                else:
                    MY_LOGGER.debug('Skipping - %s (%s) - inactive', ping['description'], ping['ip'])
    MY_LOGGER.debug('-' * 10)

    # add in HTML header / footer
    response_html = '<h3>Local Network Connectivity</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Connection</th><th>Information</th></tr>' + \
        response_html + NEWLINE + \
        '</table>' + NEWLINE

    MY_LOGGER.debug('=' * 30)
    return response_text, response_html, response_email_required


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

EMAIL_OVERIDE = False
try:
    # extract parameters
    if sys.argv[1] == 'Y':
        EMAIL_OVERIDE = True
        MY_LOGGER.debug('Forcing email to be sent')
except IndexError as exc:
    MY_LOGGER.debug('Exception whilst parsing command line parameters: %s %s %s',
                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
    MY_LOGGER.debug('Most likely due to no args being passed - fairly safe to ignore')

# get current epoch time
CURRENT_TIME = time.time()
MY_LOGGER.debug('CURRENT_TIME = %d', CURRENT_TIME)

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]
MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

# get the run time, to use for status update date time
ALERT_INFO = get_local_date_time() + ' ' +  LOCAL_TIME_ZONE + \
        ' [' + get_utc_date_time() + ' UTC].'
MY_LOGGER.debug('ALERT_INFO = %s', ALERT_INFO)

# email and data control info
STATUS_CHANGE_DETECTED = False
EMAIL_TEXT = ''
EMAIL_HTML = ''
NEWLINE = os.linesep + os.linesep
EMAIL_SUBJECT, EMAIL_REQUIRED = get_email_info()

# load satellite info
SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'config-watchdog.json')
SATELLITE_DATA = wxcutils.load_json(WEB_PATH + 'goes/', 'last-received.json')
MY_LOGGER.debug('current SATELLITE_INFO = %s', SATELLITE_INFO)

# load server info
SERVER_INFO = wxcutils.load_json(CONFIG_PATH, 'config-watchdog-servers.json')
MY_LOGGER.debug('current SERVER_INFO = %s', SERVER_INFO)

# load network connectivity
LATESTNETWORK = wxcutils.load_json(WEB_PATH + 'goes/', 'network.json')
PREVIOUSTNETWORK = wxcutils.load_json(CONFIG_PATH, 'network.json')
MY_LOGGER.debug('LATESTNETWORK = %s', LATESTNETWORK)
MY_LOGGER.debug('PREVIOUSTNETWORK = %s', PREVIOUSTNETWORK)

# load satellite status
LATESTSATSTATUS = wxcutils.load_json(WEB_PATH + 'gk-2a/', 'satellite-receivers.json')
PREVIOUSSATSTATUS = wxcutils.load_json(CONFIG_PATH, 'satellite-receivers.json')
MY_LOGGER.debug('LATESTSATSTATUS = %s', LATESTSATSTATUS)
MY_LOGGER.debug('PREVIOUSSATSTATUS = %s', PREVIOUSSATSTATUS)

# load pings
PINGS = wxcutils.load_json(CONFIG_PATH, 'pings.json')
MY_LOGGER.debug('PINGS = %s', PINGS)

# max age we care about seeing updates for in minutes (1 week)
MAX_AGE = 60 * 24 * 7
MY_LOGGER.debug('MAX_AGE = %d', MAX_AGE)


# do the different checks...
MY_LOGGER.debug('Kicking off the different checks...')

# iterate through satellites on this web server
RESULT_TEXT, RESULT_HTML, RESULT_EMAIL_REQUIRED = check_webserver_images()
EMAIL_TEXT += RESULT_TEXT
EMAIL_HTML += RESULT_HTML
if RESULT_EMAIL_REQUIRED:
    EMAIL_REQUIRED = True

# iterate through satellites on data server
RESULT_TEXT, RESULT_HTML, RESULT_EMAIL_REQUIRED = check_data_server_images()
EMAIL_TEXT += RESULT_TEXT
EMAIL_HTML += RESULT_HTML
if RESULT_EMAIL_REQUIRED:
    EMAIL_REQUIRED = True

# validate space left on servers
RESULT_TEXT, RESULT_HTML, RESULT_EMAIL_REQUIRED = check_drive_space()
EMAIL_TEXT += RESULT_TEXT
EMAIL_HTML += RESULT_HTML
if RESULT_EMAIL_REQUIRED:
    EMAIL_REQUIRED = True

# validate satellite status
RESULT_TEXT, RESULT_HTML, RESULT_EMAIL_REQUIRED = check_sat_status()
EMAIL_TEXT += RESULT_TEXT
EMAIL_HTML += RESULT_HTML
if RESULT_EMAIL_REQUIRED:
    EMAIL_REQUIRED = True
# save latest
wxcutils.save_json(CONFIG_PATH, 'satellite-receivers.json', LATESTSATSTATUS)

# validate network connectivity
RESULT_TEXT, RESULT_HTML, RESULT_EMAIL_REQUIRED = check_network()
EMAIL_TEXT += RESULT_TEXT
EMAIL_HTML += RESULT_HTML
if RESULT_EMAIL_REQUIRED:
    EMAIL_REQUIRED = True
# save latest
wxcutils.save_json(CONFIG_PATH, 'network.json', LATESTNETWORK)

# # validate ping connectivity
RESULT_TEXT, RESULT_HTML, RESULT_EMAIL_REQUIRED = check_pings()
EMAIL_TEXT += RESULT_TEXT
EMAIL_HTML += RESULT_HTML
if RESULT_EMAIL_REQUIRED:
    EMAIL_REQUIRED = True
# save latest
wxcutils.save_json(CONFIG_PATH, 'pings.json', PINGS)

# send the email, if required
MY_LOGGER.debug('=' * 30)
if EMAIL_REQUIRED or EMAIL_OVERIDE:
    MY_LOGGER.debug('Email required...')

    MY_LOGGER.debug('Saving updated config')
    MY_LOGGER.debug('Sending Email')
    if not send_email(EMAIL_TEXT, EMAIL_HTML, 'email.json'):
        # try with alternate email
        MY_LOGGER.debug('Sending Email using alternate server')
        if not send_email(EMAIL_TEXT, EMAIL_HTML, 'email2.json'):
            MY_LOGGER.debug('Sending Email using alternate server also failed')
        else:
            MY_LOGGER.debug('Sending Email using alternate server worked')

    # save the new sat info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog.json', SATELLITE_INFO)
    # save the new server info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog-servers.json', SERVER_INFO)
else:
    MY_LOGGER.debug('No status changes so email not required...')
MY_LOGGER.debug('=' * 30)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')