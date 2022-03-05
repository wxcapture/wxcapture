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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import wxcutils


def check_ip(address):
    """Check if IP address responds to pings"""
    cmd = Popen(['ping', address, '-c', '1', '-W', '1']
                , stdout=PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    MY_LOGGER.debug('stdout = %s', stdout.decode('utf-8'))
    MY_LOGGER.debug('stderr = %s', stderr.decode('utf-8'))
    if '100% packet loss' in stdout.decode('utf-8'):
        return False
    return True


def validate_file(vf_si):
    """see if an image was created in a suitable
    time period"""
    MY_LOGGER.debug('vf_si = %s', vf_si)

    vf_status = 'good'
    vf_text = ''
    vf_html = ''
    vf_data = ''

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

    vf_data = vf_si['Display Name'] + ',' + str(CURRENT_TIME) + ',' + ALERT_INFO + ',' + \
        vf_si['Max Age'] + ',' + vf_age_text + ',' + vf_margin_text + ',' + \
        vf_change + ',' + vf_status + '\r\n'

    return vf_status, vf_text, vf_html, vf_data


def validate_server(vs_si):
    """validate server space used"""
    MY_LOGGER.debug('vs_si = %s', vs_si)

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

    vs_data = vs_si['Display Name'] + ',' + str(CURRENT_TIME) + ',' + ALERT_INFO + ',' + \
        vs_si['Max Used'] + ',' + vs_space_used + ',' + vs_margin + ',' + \
        vs_change + ',' + vs_status + '\r\n'

    return vs_status, vs_text, vs_html, vs_data


def send_email(se_text0, se_html0, se_text1, se_html1, se_text2, se_html2, se_text3, se_html3, se_text4, se_html4, se_text5, se_html5, se_config_file):
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
    se_text = EMAIL_SUBJECT + ' - ' + ALERT_INFO + NEWLINE + \
        se_text0 + NEWLINE + \
        se_text1 + NEWLINE + \
        se_text2 + NEWLINE + \
        se_text3 + NEWLINE + \
        se_text4 + NEWLINE + \
        se_text5 + NEWLINE + \
        'Last status change on ' + ALERT_INFO
    MY_LOGGER.debug('se_text = %s', se_text)

    # html text
    se_html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + \
        '<html><head>' + \
        '<title>Watchdog - ' + EMAIL_SUBJECT + '</title></head>' + NEWLINE + \
        '<body><h2>' + EMAIL_SUBJECT + ' - ' + ALERT_INFO + '</h2>' + NEWLINE + \
        '<h3>Satellites - Web Server</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
        se_html0 + \
        '</table>' + NEWLINE + \
        '<h3>Satellites - Data Server</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Satellite</th><th>Threshold (min)</th><th>Age (min)</th><th>Delta (min)</th></tr>' + \
        se_html1 + \
        '</table>' + NEWLINE + \
        '<h3>Servers</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Server</th><th>Max Used (percent)</th><th>Used (percent)</th><th>Delta (percent)</th></tr>' + \
        se_html2 + \
        '</table>' + NEWLINE +\
        '<h3>Network</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Connection</th><th>Information</th><th>Date</th></tr>' + \
        se_html3 + \
         '</table>' + NEWLINE +\
        '<h3>Satellite Lock</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Connection</th><th>Lock?</th><th>Skipped Symbols</th><th>Reed Solomon Errors</th><th>Viterbi Errors</th><th>Date</th></tr>' + \
        se_html4 + \
         '</table>' + NEWLINE +\
        '<h3>Pings</h3>' + \
        '<table border="1">' + \
        '<tr><th>Status</th><th>Status Change?</th><th>Connection</th><th>Information</th><th>Date</th></tr>' + \
        se_html5 + \
         '</table>' + NEWLINE +\
        '<p>Last status change on ' + ALERT_INFO + '</p>' + \
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
EMAIL_TEXT = ''
EMAIL_HTML = ''
EMAIL_TEXT2 = ''
EMAIL_HTML2 = ''
CSV_DATA = ''
CSV_DATA2 = ''
NEWLINE = os.linesep + os.linesep

HOURS = int(time.strftime('%H'))
MINUTES = int(time.strftime('%M'))

# send status update on first run in a day
# otherwise only send on a status change
if (HOURS == 0) and ( 1 < MINUTES < 14):
    MY_LOGGER.debug('Daily update email')
    EMAIL_SUBJECT = 'Daily Update'
    EMAIL_REQUIRED = True
else:
    MY_LOGGER.debug('Status change email')
    EMAIL_SUBJECT = 'Status Change'
    EMAIL_REQUIRED = False

# load satellite info
SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'config-watchdog.json')
SATELLITE_DATA = wxcutils.load_json(WEB_PATH + 'goes/', 'last-received.json')
# MY_LOGGER.debug('current SATELLITE_INFO = %s', SATELLITE_INFO)

# get the run time, to use for status update date time
ALERT_INFO = get_local_date_time() + ' ' +  LOCAL_TIME_ZONE + \
        ' [' + get_utc_date_time() + ' UTC].'
MY_LOGGER.debug('ALERT_INFO = %s', ALERT_INFO)

# iterate through satellites on this server
MY_LOGGER.debug('-' * 20)
MY_LOGGER.debug('Iterate through satellites on this server')
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
            MY_LOGGER.debug('Status change detected - old = %s, new = %s',
                            si['Last Status'], status)
            si['Last Status'] = status
            si['Status Change'] = ALERT_INFO
        EMAIL_TEXT += text
        EMAIL_HTML += html
        CSV_DATA += data
    else:
        MY_LOGGER.debug('Satellite is not active')

MY_LOGGER.debug('-' * 20)

# iterate through satellites on data server
MY_LOGGER.debug('-' * 20)
MY_LOGGER.debug('Iterate through satellites on data server')
EMAIL_TEXT1 = ''
EMAIL_HTML1 = ''
for sd in SATELLITE_DATA:
    MY_LOGGER.debug('Satellite = %s', sd['Display Name'])
    if sd['Last Status'] == 'OK':
        msg = ' is within the receiving threshold ('
        sat_status = '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>' 
    else:
        msg = ' has exceeded the receiving threshold ('
        sat_status = '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'
    if sd['Current Age'] != 'n/a':
        margin = str(int(sd['Max Age']) - int(sd['Current Age']))
    else:
        margin = 'n/a'
    EMAIL_TEXT1 += sd['Last Status'] + ' ' + sd['Display Name'] + msg + \
            sd['Max Age'] + ' min) with age of ' + sd['Current Age'] + \
            ' min - safety margin ' + margin + ' min' + \
            NEWLINE
    EMAIL_HTML1 += sat_status + \
        '<td align=\"center\">' + sd['Status Change'] + '</td>' +\
        '<td align=\"center\">' + sd['Display Name'] + '</td>' +\
        '<td align=\"center\">' + sd['Max Age'] + '</td>' +\
        '<td align=\"center\">' + sd['Current Age'] + '</td>' +\
        '<td align=\"center\">' + margin + '</td></tr>' + NEWLINE

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
            MY_LOGGER.debug('Status change detected - old = %s, new = %s',
                            si['Last Status'], status)
            si['Last Status'] = status
            si['Status Change'] = ALERT_INFO
        EMAIL_TEXT2 += text
        EMAIL_HTML2 += html + NEWLINE
        CSV_DATA2 += data
    else:
        MY_LOGGER.debug('Server is not active')

MY_LOGGER.debug('-' * 20)

# write data to the csv files
write_data()

# validate network connectivity
MY_LOGGER.debug('-' * 20)
LATESTNETWORK = wxcutils.load_json(WEB_PATH + 'goes/', 'network.json')
PREVIOUSTNETWORK = wxcutils.load_json(CONFIG_PATH, 'network.json')

EMAIL_TEXT3 = ''
EMAIL_HTML3 = ''
PREVIOUS = ''

for key, value in LATESTNETWORK.items():
    if key == 'addresses':
        for nc in LATESTNETWORK[key]:
            if nc['Active'] == 'yes':
                MY_LOGGER.debug('-' * 20)
                MY_LOGGER.debug(nc)
                if nc['status'] == 'OK':
                    EMAIL_HTML3 += '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
                else:
                    EMAIL_HTML3 += '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'

                # get the previous state
                for key2, value2 in PREVIOUSTNETWORK.items():
                    if key2 == 'addresses':
                        for nc2 in PREVIOUSTNETWORK[key]:
                            if nc['description'] == nc2['description']:
                                PREVIOUS = nc2
                                MY_LOGGER.debug('Previous = %s', PREVIOUS)


                CHANGE = 'N'
                if nc['status'] != PREVIOUS['status']:
                    EMAIL_REQUIRED = True
                    CHANGE = 'Y'
                EMAIL_HTML3 += '<td align = \"center\">' + CHANGE + '</td>'

                EMAIL_TEXT3 += nc['description'] + ' - '
                EMAIL_HTML3 += '<td>' + nc['description'] + '</td>'

                if nc['status'] == 'OK':
                    EMAIL_TEXT3 += 'OK - network connectivity is good' + ' - '
                    EMAIL_HTML3 += '<td>Good connectivity</td><td>' + \
                        wxcutils.epoch_to_local(nc['when'], '%m/%d/%Y %H:%M') + '</td></tr>' + NEWLINE
                else:
                    EMAIL_TEXT3 = 'Error - network connecitivity issue - ' + nc['status'] + ''
                    EMAIL_HTML3 += '<td>' + nc['status'] + '</td><td>' + \
                        wxcutils.epoch_to_local(nc['when'], '%m/%d/%Y %H:%M') + '</td></tr>' + NEWLINE

MY_LOGGER.debug('HTML = ' + EMAIL_HTML3)
MY_LOGGER.debug('txt = ' + EMAIL_TEXT3)

# save last
wxcutils.save_json(CONFIG_PATH, 'network.json', LATESTNETWORK)

# validate satellite status
MY_LOGGER.debug('-' * 20)
LATESTSATSTATUS = wxcutils.load_json(WEB_PATH + 'gk-2a/', 'satellite-receivers.json')
PREVIOUSSATSTATUS = wxcutils.load_json(CONFIG_PATH, 'satellite-receivers.json')

EMAIL_TEXT4 = ''
EMAIL_HTML4 = ''
PREVIOUS = ''

for si1 in LATESTSATSTATUS:
    MY_LOGGER.debug('-' * 20)
    MY_LOGGER.debug('Processing - %s', si1['label'])
    MY_LOGGER.debug('si1 %s', si1)
    
    for si2 in PREVIOUSSATSTATUS:
        if si1['label'] == si2['label']:
            MY_LOGGER.debug('si2 %s', si2)
            if si1['ok'] == 'Locked':
                EMAIL_HTML4 += '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
            else:
                EMAIL_HTML4 += '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'

            CHANGE = 'N'
            if si1['ok'] != si2['ok']:
                EMAIL_REQUIRED = True
                CHANGE = 'Y'
            EMAIL_HTML4 += '<td align = \"center\">' + CHANGE + '</td>'

            EMAIL_TEXT4 +=  si1['label'] + ' - ' + si1['ok'] + ' - ' + \
                str(si1['skipped_symbols']) + ' - ' + \
                str(si1['reed_solomon_errors']) + ' - ' + str(si1['viterbi_errors']) + \
                ' - ' + wxcutils.epoch_to_local(si1['when'], '%m/%d/%Y %H:%M') + ' - '
            EMAIL_HTML4 += '<td>' +  si1['label'] + '</td><td>' + si1['ok'] + '</td><td align=\"center\">' + \
                str(si1['skipped_symbols']) + \
                '</td><td align=\"center\">' + str(si1['reed_solomon_errors']) + '</td><td align=\"center\">' + \
                str(si1['viterbi_errors']) + '</td><td>' + \
                wxcutils.epoch_to_local(si1['when'], '%m/%d/%Y %H:%M') + '</td></tr>' + NEWLINE

MY_LOGGER.debug('HTML = ' + EMAIL_HTML4)
MY_LOGGER.debug('txt = ' + EMAIL_TEXT4)

# save last
wxcutils.save_json(CONFIG_PATH, 'satellite-receivers.json', LATESTSATSTATUS)

# validate ping connectivity
MY_LOGGER.debug('-**' * 20)
PINGS = wxcutils.load_json(CONFIG_PATH, 'pings.json')
MY_LOGGER.debug('Testing Pings')
MY_LOGGER.debug(PINGS)
EMAIL_TEXT5 = ''
EMAIL_HTML5 = ''
PREVIOUS = ''

for key, value in PINGS.items():
    if key == 'addresses':
        for ping in PINGS[key]:
            if ping['Active'] == 'yes':
                new_status = 'ERROR'
                if check_ip(ping['ip']):
                    new_status = 'OK'
                MY_LOGGER.debug('-' * 20)
                MY_LOGGER.debug(ping)
                MY_LOGGER.debug('new_status = %s', new_status)
                if new_status == 'OK':
                    EMAIL_HTML5 += '<tr><td style=\"background-color:#00FF00\" align=\"center\">OK</td>'
                else:
                    EMAIL_HTML5 += '<tr><td style=\"background-color:#FF0000\" align=\"center\">ERROR</td>'

                # get the previous state
                MY_LOGGER.debug('Previous status = %s', ping['status'])
                CHANGE = 'N'
                if new_status != ping['status']:
                    EMAIL_REQUIRED = True
                    CHANGE = 'Y'
                EMAIL_HTML5 += '<td align = \"center\">' + CHANGE + '</td>'
                ping['status'] = new_status

                EMAIL_TEXT5 += ping['description'] + ' - '
                EMAIL_HTML5 += '<td>' + ping['description'] + '</td>'

                if new_status == 'OK':
                    EMAIL_TEXT5 += 'OK - network connectivity is good' + NEWLINE
                    EMAIL_HTML5 += '<td>Good connectivity</td><td>' + \
                        wxcutils.epoch_to_local(ping['when'], '%m/%d/%Y %H:%M') + '</td></tr>' + NEWLINE
                else:
                    EMAIL_TEXT5 = 'Error - network connecitivity issue  is bad' + NEWLINE
                    EMAIL_HTML5 += '<td>Bad connectivity</td><td>' + \
                        wxcutils.epoch_to_local(ping['when'], '%m/%d/%Y %H:%M') + '</td></tr>' + NEWLINE

MY_LOGGER.debug('HTML = ' + EMAIL_HTML5)
MY_LOGGER.debug('txt = ' + EMAIL_TEXT5)

# save last
wxcutils.save_json(CONFIG_PATH, 'pings.json', PINGS)


MY_LOGGER.debug('-' * 20)
if EMAIL_REQUIRED:
    MY_LOGGER.debug('Email required...')

    MY_LOGGER.debug('Saving updated config')
    MY_LOGGER.debug('Sending Email')
    if not send_email(EMAIL_TEXT, EMAIL_HTML, EMAIL_TEXT1, EMAIL_HTML1, EMAIL_TEXT2, EMAIL_HTML2, EMAIL_TEXT3, EMAIL_HTML3, EMAIL_TEXT4, EMAIL_HTML4, EMAIL_TEXT5, EMAIL_HTML5, 'email.json'):
        # try with alternate email
        MY_LOGGER.debug('Sending Email using alternate server')
        if not send_email(EMAIL_TEXT, EMAIL_HTML, EMAIL_TEXT1, EMAIL_HTML1, EMAIL_TEXT2, EMAIL_HTML2, EMAIL_TEXT3, EMAIL_HTML3, EMAIL_TEXT4, EMAIL_HTML4, EMAIL_TEXT5, EMAIL_HTML5, 'email2.json'):
            MY_LOGGER.debug('Sending Email using alternate server also failed')
        else:
            MY_LOGGER.debug('Sending Email using alternate server worked')

    # save the new sat info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog.json', SATELLITE_INFO)
    # save the new server info
    wxcutils.save_json(CONFIG_PATH, 'config-watchdog-servers.json', SERVER_INFO)



else:
    MY_LOGGER.debug('No status changes so email not required...')
MY_LOGGER.debug('-' * 20)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
