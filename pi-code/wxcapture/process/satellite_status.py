#!/usr/bin/env python3
"""build satellite status page"""


# import libraries
import os
import sys
import time
import json
import subprocess
from urllib.request import urlopen
import wxcutils


def parse(line):
    """parse line to str"""
    result = line
    return result.decode('utf-8').replace(' ', '').replace('<td>', '').replace('</td>', '').rstrip()


def scp_files():
    """scp files"""
    MY_LOGGER.debug('using scp')
    # load config
    scp_config = wxcutils.load_json(CONFIG_PATH, 'config-scp.json')
    wxcutils.run_cmd('scp ' + OUTPUT_PATH + 'satellitestatus.html ' +
                     scp_config['remote user'] + '@' +
                     scp_config['remote host'] + ':' + scp_config['remote directory'] + '/')


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

        # MY_LOGGER.debug('Parse = %s', cv_files_info[cv_filename])
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
                    MY_LOGGER.debug('||| NOT')
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

def get_page(page_url):
    """get the satellite status"""
    MY_LOGGER.debug('Getting page content')
    page_content = ''
    with urlopen(page_url) as file_in:
        page_content = file_in.read()
    # MY_LOGGER.debug('content = %s', page_content)
    return page_content


def get_noaa_status(satellite):
    """get the satellite status for a NOAA satellite"""
    def tidy_up_apt(entry):
        entry = entry.decode('utf-8')
        pos = entry.find('</strong>')
        return entry[pos + 10:pos + 13]
    def tidy_up_apt2(entry):
        entry = entry.decode('utf-8')
        pos_1_st = entry.find('VTX-1') + 85
        pos_1_end = entry.find('MHz')
        pos_2_st = entry.find('VTX-2') + 85
        pos_2_end = entry.find('MHz')
        return entry[pos_1_st:pos_1_end + 3] + \
            entry[pos_2_st:pos_2_end + 3]
    MY_LOGGER.debug('Getting %s status', satellite)
    lines = NOAA_STATUS_PAGE.splitlines()

    line_num = 0
    size_of_lines = len(lines)

    result = ''
    match = '<!-- Place Status Includes for ' + satellite + ' here --> '
    MY_LOGGER.debug('Matching to %s', match)

    while line_num < size_of_lines:
        if match in lines[line_num].decode('utf-8'):
            # found our satellite
            MY_LOGGER.debug('Found entry for %s', satellite)
            result += 'APT Status = ' + tidy_up_apt(lines[line_num + 29]) + '<br>' + \
                'Frequency = ' + tidy_up_apt2(lines[line_num + 29])
            line_num = size_of_lines
        line_num += 1
    MY_LOGGER.debug('result = %s', result)
    return result


def get_iss_status():
    """get the ISS SSTV status from ARISS"""
    page = ISS_STATUS_PAGE.decode('utf-8')
    result = ''
    start_pos = page.find('<h2 class=\'date-header\'><span>') + 30
    end_pos = page.find('</span>', start_pos)
    result += page[start_pos: end_pos] + '<br><br>'

    # find the marker for the latest update
    start_pos = page.find('<div class=\'post-body entry-content\'')
    # find the end of the div
    start_pos_2 = page.find('>', start_pos) + 1
    # find the end of the content
    end_pos = page.find('<div style=', start_pos_2)
    result += page[start_pos_2: end_pos]

    MY_LOGGER.debug('ISS text = %s', result)
    return result


def get_meteor_status(satellite):
    """get the satellite status for a Meteor satellite"""
    def tidy_up(entry):
        return entry.decode('utf-8').replace('<td>', '').replace('</td>', '').replace('                        ', '')
    MY_LOGGER.debug('Getting %s status', satellite)
    lines = METEOR_STATUS_PAGE.splitlines()

    line_num = 0
    size_of_lines = len(lines)

    result = ''
    match = '<h2>' + satellite + ':</h2>'
    MY_LOGGER.debug('Matching to %s', match)

    while line_num < size_of_lines:
        if match in lines[line_num].decode('utf-8'):
            # found our satellite
            MY_LOGGER.debug('Found entry for %s', satellite)
            result += 'Status = ' + tidy_up(lines[line_num + 11]) + '<br>' + \
                'Frequency = ' + tidy_up(lines[line_num + 9]) + '<br>' + \
                'Symbol = ' + tidy_up(lines[line_num + 10]) + '<br>' + \
                'Blue visible (64) = ' + tidy_up(lines[line_num + 19]) + '<br>' + \
                'Green visible (65) = ' + tidy_up(lines[line_num + 20]) + '<br>' + \
                'Red visible (66) = ' + tidy_up(lines[line_num + 21]) + '<br>' + \
                'Infrared #1 (67) = ' + tidy_up(lines[line_num + 29]) + '<br>' + \
                'Infrared #2 (68) = ' + tidy_up(lines[line_num + 30]) + '<br>' + \
                'Infrared #3 (69) = ' + tidy_up(lines[line_num + 31])
            line_num = size_of_lines
        line_num += 1
    MY_LOGGER.debug('result = %s', result)
    return result


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
MODULE = 'satellite_status'
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
    # grap the status web pages
    METEOR_STATUS_PAGE = get_page('http://happysat.nl/Meteor/html/Meteor_Status.html')
    NOAA_STATUS_PAGE = get_page('https://www.ospo.noaa.gov/Operations/POES/status.html')
    ISS_STATUS_PAGE = get_page('http://ariss-sstv.blogspot.com/')

    # config validation
    CONFIG_ERRORS, CONFIG_HTML = config_validation()

    # output as html
    MY_LOGGER.debug('Build webpage')
    with open(OUTPUT_PATH + 'satellitestatus.html', 'w') as html:
        # html header
        html.write('<!DOCTYPE html>')
        html.write('<html lang=\"en\"><head>'
                   '<meta charset=\"UTF-8\">'
                   '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                   '<meta name=\"description\" content=\"Satellite transmission status for Meteor-M and NOAA weather satellites, International Space Station (ISS) SSTV and WxCapture Twitter Feed\">'
                   '<meta name=\"keywords\" content=\"wxcapture, weather, satellite, NOAA, Meteor, images, ISS, Zarya, SSTV, Amsat, orbit, APT, LRPT, SDR, Mike, KiwiinNZ, Albert, Technobird22, Predictions, Auckland, New Zealand, storm, cyclone, hurricane, front, rain, wind, cloud\">'
                   '<meta name=\"author\" content=\"WxCapture\">'
                   '<title>Satellite Status</title>'
                   '<link rel=\"stylesheet\" href=\"css/styles.css\">'
                   '<link rel=\"shortcut icon\" type=\"image/png\" href=\"/wxcapture/favicon.png\"/>')
        html.write('</head>')
        html.write('<body onload=\"defaulthide()\">')
        html.write(wxcutils.load_file(CONFIG_PATH, 'main-header.txt').replace('PAGE-TITLE',
                                                                              'Satellite Status'))
        html.write('<section class=\"content-section container\">')

        html.write('<h2 class=\"section-header\">Meteor-M Series Status</h2>')
        html.write('<table>')
        html.write('<tr><th>Meteor-M N2</th><th>Meteor-M N2-2</th></tr>')
        html.write('<tr><td>' + get_meteor_status('Meteor-M N2') + '</td>')
        html.write('<td>' + get_meteor_status('Meteor-M N2-2') + '</td></tr>')
        html.write('</table>')
        html.write('<p><a href=\"http://happysat.nl/Meteor/html/Meteor_Status.html\" target=\"_blank\" rel=\"noopener\">Data source</a></p>')
        html.write('</section>')

        html.write('<section class=\"content-section container\">')
        html.write('<h2 class=\"section-header\">NOAA Series Status</h2>')
        html.write('<table>')
        html.write('<tr><th>NOAA 15</th><th>NOAA 18</th><th>NOAA 19</th></tr>')
        html.write('<tr><td>' + get_noaa_status('NOAA 15') + '</td>')
        html.write('<td>' + get_noaa_status('NOAA 18') + '</td>')
        html.write('<td>' + get_noaa_status('NOAA 19') + '</td></tr>')
        html.write('</table>')
        html.write('<p><a href=\"https://www.ospo.noaa.gov/Operations/POES/status.html\" target=\"_blank\" rel=\"noopener\">Data source</a></p>')
        html.write('</section>')

        html.write('<section class=\"content-section container\">')
        html.write('<h2 class=\"section-header\">ISS SSTV - ARISS Status</h2>')
        html.write('<table>')
        html.write('<tr><th>ISS Zarya</th></tr>')
        html.write('<tr><td>' + get_iss_status() + '</td></tr>')
        html.write('</table>')
        html.write('<p><a href=\"http://ariss-sstv.blogspot.com/\" target=\"_blank\" rel=\"noopener\">Data source</a></p>')
        html.write('</section>')

        # load NOAA and Meteor options
        NOAA_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-NOAA.json')
        METEOR_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-METEOR.json')
        # if either configured for tweeting, include tweet config info
        if NOAA_OPTIONS['tweet'] == 'yes' or METEOR_OPTIONS['tweet'] == 'yes':
            TWITTER_CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-twitter.json')
            html.write('<section class=\"content-section container\">')
            html.write('<h2 class=\"section-header\">Twitter Feed</h2>')
            html.write('<p>Tweeting images to <a href=\"https://twitter.com/' + TWITTER_CONFIG['tweet to'].replace('@', '') + '\" target=\"_blank\" rel=\"noopener\">' + TWITTER_CONFIG['tweet to'] + '</a> for:</p><ul>')
            if NOAA_OPTIONS['tweet'] == 'yes':
                html.write('<li>NOAA - enhancement option = ' + NOAA_OPTIONS['tweet enhancement'] + '</li>')
            if METEOR_OPTIONS['tweet'] == 'yes':
                html.write('<li>METEOR - thumbnail (full size images are too large for Twitter)</li>')
            html.write('</ul></section>')

        # config validation results
        html.write('<section class=\"content-section container\">')
        html.write('<h2 class=\"section-header\">WxCapture Configuration Validation</h2>')
        html.write('<button onclick=\"hideshow()\" id=\"showhide\" class=\"showhidebutton\">Show configuration</button>')
        if CONFIG_ERRORS:
            html.write('<h1>Configuration Error(s) Detected - Validate Config!</h1>')
        html.write('<div id=\"configurationDiv\">')
        html.write('<p>Please review any rows highlighted and update the associated configuration file.</p>')

        html.write(CONFIG_HTML)
        html.write('</ul></section>')
        html.write('</div>')

        # footer
        html.write('<footer class=\"main-footer\">')
        html.write('<p id=\"footer-text\">Satellite Status last updated at <span class=\"time\">' +
                   time.strftime('%H:%M (' +
                                 subprocess.check_output("date").
                                 decode('utf-8').split(' ')[-2] +
                                 ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
                   '.</p>')
        html.write('</footer>')

        html.write('<script>')
        html.write('function hideshow() {')
        html.write('  var x = document.getElementById(\"configurationDiv\");')
        html.write('  if (x.style.display === \"none\") {')
        html.write('    x.style.display = \"block\";')
        html.write('   showhide.innerHTML = \"Hide configuration\";')
        html.write(' } else {')
        html.write('   x.style.display = \"none\";')
        html.write('   showhide.innerHTML = \"Show configuration\";')
        html.write(' }')
        html.write('}')
        html.write('function defaulthide() {')
        html.write('  var x = document.getElementById(\"configurationDiv\");')
        html.write('  x.style.display = \"none\";')
        html.write('  showhide.innerHTML = \"Show configuration\";')
        html.write('}')
        html.write('</script>')

        html.write('</body></html>')

    # acp file to destination
    MY_LOGGER.debug('SCP files')
    scp_files()
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
