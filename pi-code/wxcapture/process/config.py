#!/usr/bin/env python3
"""build config status page"""


# import libraries
import os
import sys
import time
import json
import subprocess
from subprocess import Popen, PIPE
import wxcutils


def parse(line):
    """parse line to str"""
    result = line
    return result.decode('utf-8').replace(' ', '').replace('<td>', '').replace('</td>', '').rstrip()


def migrate_files():
    """migrate files to server"""
    MY_LOGGER.debug('migrating files')
    files_to_copy = []
    files_to_copy.append({'source path': OUTPUT_PATH, 'source file': 'config.html', 'destination path': '', 'copied': 'no'})
    MY_LOGGER.debug('Files to copy = %s', files_to_copy)
    wxcutils.migrate_files(files_to_copy)
    MY_LOGGER.debug('Completed migrating files')


def valid_json_file(vjf_file):
    """validate if a json file is a valid json file"""
    MY_LOGGER.debug('valid_json_file for %s', vjf_file)
    try:
        vjf_json = wxcutils.load_file(CONFIG_PATH, vjf_file)
        # MY_LOGGER.debug('json = %s', vjf_json)
        json.loads(vjf_json)
    except ValueError:
        MY_LOGGER.debug('valid_json_file exception handler: %s %s %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        return False
    return True


def config_validation():
    """config"""

    def is_number(test_num):
        try:
            float(test_num)
            return True
        except ValueError:
            return False

    cv_errors_found = False
    cv_results = ''

    cv_files_info = wxcutils.load_json(CONFIG_PATH, 'config-validation.json')
    cv_results += '<h3>File Level Checks</h3><table><tr><th>Filename</th><th>Description</th><th>Required</th><th>Found</th><th>Valid JSON</th><th>Errors</th></tr>'
    for cv_filename in cv_files_info:
        MY_LOGGER.debug('cv_filename = %s', cv_filename)
        MY_LOGGER.debug('description %s', cv_files_info[cv_filename]['description'])
        MY_LOGGER.debug('required %s', cv_files_info[cv_filename]['required'])
        cv_error = ''
        cv_files_info[cv_filename]['exists'] = 'no'
        if os.path.isfile(CONFIG_PATH + cv_filename):
            cv_files_info[cv_filename]['exists'] = 'yes'
        if cv_files_info[cv_filename]['exists'] != 'yes' and cv_files_info[cv_filename]['required'] == 'yes':
            cv_error = 'Required file is missing'
        cv_files_info[cv_filename]['valid json'] = 'no'
        if valid_json_file(cv_filename):
            cv_files_info[cv_filename]['valid json'] = 'yes'
        if cv_error == '':
            cv_error = '(none)'
            cv_results += '<tr>'
        else:
            cv_results += '<tr class=\"row-highlight\">'
            cv_errors_found = True
        cv_results += '<td>' + cv_filename + '</td><td>' + cv_files_info[cv_filename]['description'] + '</td><td>' + \
            cv_files_info[cv_filename]['required'] + '</td><td>' + cv_files_info[cv_filename]['exists'] + '</td><td>' + \
            cv_files_info[cv_filename]['valid json'] + '</td><td>' + cv_error + '</td></tr>'
    cv_results += '</table>'

    for cv_filename in cv_files_info:
        cv_results += '<h3>Content Checks - ' + cv_filename + '</h3><table><tr><th>Key</th><th>Value</th><th>Description</th><th>Required</th><th>Found</th><th>Valid Values</th><th>Errors</th></tr>'
        cv_test_file = wxcutils.load_json(CONFIG_PATH, cv_filename)

        MY_LOGGER.debug('Parse = %s', cv_files_info[cv_filename])

        if cv_filename in ('sdr.json', 'satellites.json'):
            MY_LOGGER.debug('sdr and satellites specific checking - %s', cv_filename)

            cv_field_entry = ''
            if cv_filename == 'sdr.json':
                cv_field_entry = 'sdr'
            if cv_filename == 'satellites.json':
                cv_field_entry = 'satellites'

            # for every entity
            MY_LOGGER.debug('looping through entities - %s', cv_field_entry)
            for cv_file_row1 in cv_test_file[cv_field_entry]:
                MY_LOGGER.debug('cv_file_row1 = %s', cv_file_row1)
                cv_name = ''

                for cv_row in cv_files_info[cv_filename]['field validation']:
                    MY_LOGGER.debug('%s req = %s vv = %s desc = %s',
                                    cv_row,
                                    cv_files_info[cv_filename]['field validation'][cv_row]['required'],
                                    cv_files_info[cv_filename]['field validation'][cv_row]['valid values'],
                                    cv_files_info[cv_filename]['field validation'][cv_row]['description'])
                    cv_error = ''
                    try:
                        cv_value = str(cv_file_row1[cv_row])
                        if cv_row == 'name':
                            cv_name = cv_value
                        cv_found = 'yes'
                        cv_error = ''
                    except KeyError:
                        MY_LOGGER.debug('config_validation exception handler - value missing: %s %s %s',
                                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                        cv_value = ''
                        cv_found = 'no'
                        cv_error += 'Field missing from file. '
                    if cv_value == '' and cv_files_info[cv_filename]['field validation'][cv_row]['required'] == 'yes':
                        cv_error += 'Required value is missing. '
                    cv_valid_values = cv_files_info[cv_filename]['field validation'][cv_row]['valid values']
                    if cv_valid_values == '-pattern-':
                        cv_valid_values = 'The value must follow the pattern, as shown in the description'
                    if cv_valid_values == '-number-':
                        cv_valid_values = 'The value must be a number, as shown in the description'
                        if not is_number(cv_value):
                            cv_error += 'Value is not a number. '
                    if cv_valid_values == '-any-':
                        cv_valid_values = 'The value can have any value, as shown in the description'
                    if '|' in cv_valid_values:
                        if not cv_value in cv_valid_values:
                            cv_error += 'Value is not a valid value'
                        cv_valid_values = 'Valid values, separated by a \'|\' are: ' + cv_valid_values
                    if cv_error == '':
                        cv_error = '(none)'
                        cv_results += '<tr>'
                    else:
                        cv_results += '<tr class=\"row-highlight\">'
                        cv_errors_found = True
                    if cv_files_info[cv_filename]['field validation'][cv_row]['hidden'] == 'yes':
                        cv_value = '*hidden*'
                    cv_results += '<td>' + cv_name + ' - ' + cv_row + '</td>'
                    cv_results += '<td>' + cv_value + '</td>'
                    cv_results += '<td>' + cv_files_info[cv_filename]['field validation'][cv_row]['description'] + '</td>'
                    cv_results += '<td>' + cv_files_info[cv_filename]['field validation'][cv_row]['required'] + '</td>'
                    cv_results += '<td>' + cv_found  + '</td>'
                    cv_results += '<td>' + cv_valid_values + '</td>'
                    cv_results += '<td>' + cv_error + '</td></tr>'
        else:
            for cv_row in cv_files_info[cv_filename]['field validation']:
                MY_LOGGER.debug('%s %s %s',
                                cv_files_info[cv_filename]['field validation'][cv_row]['required'],
                                cv_files_info[cv_filename]['field validation'][cv_row]['valid values'],
                                cv_files_info[cv_filename]['field validation'][cv_row]['description'])
                cv_error = ''
                try:
                    MY_LOGGER.debug('testing field %s', cv_row)
                    cv_value = str(cv_test_file[cv_row])
                    cv_found = 'yes'
                    cv_error = ''
                except KeyError:
                    MY_LOGGER.debug('config_validation exception handler - value missing: %s %s %s',
                                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
                    cv_value = ''
                    cv_found = 'no'
                    cv_error += 'Field missing from file. '
                if cv_value == '' and cv_files_info[cv_filename]['field validation'][cv_row]['required'] == 'yes':
                    cv_error += 'Required value is missing. '
                cv_valid_values = cv_files_info[cv_filename]['field validation'][cv_row]['valid values']
                if cv_valid_values == '-pattern-':
                    cv_valid_values = 'The value must follow the pattern, as shown in the description'
                if cv_valid_values == '-number-':
                    cv_valid_values = 'The value must be a number, as shown in the description'
                    if not is_number(cv_value):
                        cv_error += 'Value is not a number. '
                if cv_valid_values == '-any-':
                    cv_valid_values = 'The value can have any value, as shown in the description'
                if '|' in cv_valid_values:
                    if not cv_value in cv_valid_values:
                        cv_error += 'Value is not a valid value'
                    cv_valid_values = 'Valid values, separated by a \'|\' are: ' + cv_valid_values
                if cv_error == '':
                    cv_error = '(none)'
                    cv_results += '<tr>'
                else:
                    cv_results += '<tr class=\"row-highlight\">'
                    cv_errors_found = True
                if cv_files_info[cv_filename]['field validation'][cv_row]['hidden'] == 'yes':
                    cv_value = '*hidden*'
                cv_results += '<td>' + cv_row + '</td>'
                cv_results += '<td>' + cv_value + '</td>'
                cv_results += '<td>' + cv_files_info[cv_filename]['field validation'][cv_row]['description'] + '</td>'
                cv_results += '<td>' + cv_files_info[cv_filename]['field validation'][cv_row]['required'] + '</td>'
                cv_results += '<td>' + cv_found  + '</td>'
                cv_results += '<td>' + cv_valid_values + '</td>'
                cv_results += '<td>' + cv_error + '</td></tr>'

        cv_results += '</table>'

        if cv_errors_found:
            MY_LOGGER.debug('Config errors found')
        else:
            MY_LOGGER.debug('No config errors found')

    return cv_errors_found, cv_results


def drive_validation(dv_config):
    """validate drive space utilisation"""
    dv_errors_found = False
    dv_space = 'unknown'

    dv_cmd = Popen(['df'], stdout=PIPE, stderr=PIPE)
    dv_stdout, dv_stderr = dv_cmd.communicate()
    MY_LOGGER.debug('stdout:%s', dv_stdout)
    MY_LOGGER.debug('stderr:%s', dv_stderr)
    dv_results = dv_stdout.decode('utf-8').splitlines()
    for dv_line in dv_results:
        if dv_config['drive space location'] in dv_line:
            dv_space = dv_line.split()[4].split('%')[0]
    MY_LOGGER.debug('dv_space  = %s', dv_space)

    dv_results = '<h3>Pi Drive Space Free = '
    if dv_space == 'unknown':
        dv_errors_found = True
        dv_results += 'not determined</h3>'
    else:
        dv_results += dv_space + '%</h3>'
        if int(dv_space) > int(dv_config['drive space error']):
            dv_results += '<h1>Drive space is critically low - urgently reduce space used</h1>'
            dv_errors_found = True
        elif int(dv_space) > int(dv_config['drive space warning']):
            dv_results += '<h1>Drive space is getting low - review space used</h1>'
            dv_errors_found = True

    MY_LOGGER.debug('dv_results = %s', dv_results)

    return dv_errors_found, dv_results


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
MODULE = 'config'
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


try:
    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    # config validation
    CONFIG_ERRORS, CONFIG_HTML = config_validation()

    # drive space validation
    DRIVE_ERRORS, DRIVE_HTML = drive_validation(CONFIG_INFO)

    # output as html
    MY_LOGGER.debug('Build webpage')
    with open(OUTPUT_PATH + 'config.html', 'w') as html:
        # html header
        html.write('<!DOCTYPE html>')
        html.write('<html lang=\"en\"><head>'
                   '<meta charset=\"UTF-8\">'
                   '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                   '<meta name=\"description\" content=\"Satellite transmission status for Meteor-M and NOAA weather satellites, International Space Station (ISS) SSTV and WxCapture Twitter Feed\">'
                   '<meta name=\"keywords\" content=\"' + CONFIG_INFO['webpage keywords'] + '\">'
                   '<meta name=\"author\" content=\"WxCapture\">'
                   '<title>configuration Status</title>'
                   '<link rel=\"stylesheet\" href=\"css/styles.css\">'
                   '<link rel=\"shortcut icon\" type=\"image/png\" href=\"' + CONFIG_INFO['Link Base'] + 'favicon.png\"/>')
        html.write('</head>')
        html.write('<body>')
        html.write(wxcutils.load_file(CONFIG_PATH, 'main-header.txt').replace('PAGE-TITLE',
                                                                              'Configuration Status'))
        html.write('<section class=\"content-section container\">')

        # config validation results
        html.write('<section class=\"content-section container\">')
        html.write('<h2 class=\"section-header\">WxCapture Configuration Validation</h2>')

        if DRIVE_ERRORS:
            html.write('<h1>Storage Space Issue Detected!</h1>')
        if CONFIG_ERRORS:
            html.write('<h1>Configuration Error(s) Detected - Validate Config!</h1>')
        html.write('<div id=\"configurationDiv\">')
        html.write(DRIVE_HTML)
        html.write('<p>Please review any rows highlighted and update the associated configuration file.</p>')
        html.write(CONFIG_HTML)
        html.write('</div>')
        html.write('</section>')

        # footer
        html.write('<footer class=\"main-footer\">')
        html.write('<p id=\"footer-text\">Satellite Status last updated at <span class=\"time\">' +
                   time.strftime('%H:%M (' +
                                 subprocess.check_output("date").
                                 decode('utf-8').split(' ')[-2] +
                                 ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
                   '.</p>')
        html.write('</footer>')

        html.write('</body></html>')

    # migrate files to destination
    MY_LOGGER.debug('migrate files')
    migrate_files()
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
