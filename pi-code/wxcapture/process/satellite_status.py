#!/usr/bin/env python3
"""build satellite status page"""


# import libraries
import os
import time
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
        pos_1_st = entry.find('VTX-1')
        pos_1_end = entry.find('MHz')
        pos_2_st = entry.find('VTX-2')
        pos_2_end = entry.find('MHz')
        return entry[pos_1_st:pos_1_end + 3].replace(' &nbsp; ', ' - ') + \
            entry[pos_2_st:pos_2_end + 3].replace(' &nbsp; ', ' - ')
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
        return entry.decode('utf-8').replace('<td>', '').replace('</td>', '')
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
                'Blue visible APID64 = ' + tidy_up(lines[line_num + 19]) + '<br>' + \
                'Green visible APID65 = ' + tidy_up(lines[line_num + 20]) + '<br>' + \
                'Red visible APID66 = ' + tidy_up(lines[line_num + 21]) + '<br>' + \
                'Infrared APID67 = ' + tidy_up(lines[line_num + 29]) + '<br>' + \
                'Infrared APID68 = ' + tidy_up(lines[line_num + 30]) + '<br>' + \
                'Infrared APID69 = ' + tidy_up(lines[line_num + 31])
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

# grap the status web pages
METEOR_STATUS_PAGE = get_page('http://happysat.nl/Meteor/html/Meteor_Status.html')
NOAA_STATUS_PAGE = get_page('https://www.ospo.noaa.gov/Operations/POES/status.html')
ISS_STATUS_PAGE = get_page('http://ariss-sstv.blogspot.com/')

# output as html
MY_LOGGER.debug('Build webpage')
with open(OUTPUT_PATH + 'satellitestatus.html', 'w') as html:
    # html header
    html.write('<!DOCTYPE html>')
    html.write('<html lang=\"en\"><head>'
               '<meta charset=\"UTF-8\">'
               '<title>Satellite Status'
               '</title>'
               '<link rel=\"stylesheet\" href=\"css/styles.css\">'
               '<link rel=\"shortcut icon\" type=\"image/png\" href=\"/wxcapture/favicon.png\"/>')
    html.write('</head>')
    html.write('<body>')
    html.write(wxcutils.load_file(CONFIG_PATH, 'main-header.txt').replace('PAGE-TITLE',
                                                                          'Satellite Status'))
    html.write('<section class=\"content-section container\">')

    html.write('<h2 class=\"section-header\">Meteor-M Series Status</h2>')
    html.write('<table>')
    html.write('<tr><th>Meteor-M N2</th><th>Meteor-M N2-2</th></tr>')
    html.write('<tr><td>' + get_meteor_status('Meteor-M N2') + '</td>')
    html.write('<td>' + get_meteor_status('Meteor-M N2-2') + '</td></tr>')
    html.write('</table>')
    html.write('<p><a href=\"http://happysat.nl/Meteor/html/Meteor_Status.html\" target=\"_blank\">Data source</a></p>')
    html.write('</section>')

    html.write('<section class=\"content-section container\">')
    html.write('<h2 class=\"section-header\">NOAA Series Status</h2>')
    html.write('<table>')
    html.write('<tr><th>NOAA 15</th><th>NOAA 18</th><th>NOAA 19</th></tr>')
    html.write('<tr><td>' + get_noaa_status('NOAA 15') + '</td>')
    html.write('<td>' + get_noaa_status('NOAA 18') + '</td>')
    html.write('<td>' + get_noaa_status('NOAA 19') + '</td></tr>')
    html.write('</table>')
    html.write('<p><a href=\"https://www.ospo.noaa.gov/Operations/POES/status.html\" target=\"_blank\">Data source</a></p>')
    html.write('</section>')

    html.write('<section class=\"content-section container\">')
    html.write('<h2 class=\"section-header\">ISS SSTV - ARISS Status</h2>')
    html.write('<table>')
    html.write('<tr><th>ISS Zarya</th></tr>')
    html.write('<tr><td>' + get_iss_status() + '</td></tr>')
    html.write('</table>')
    html.write('<p><a href=\"http://ariss-sstv.blogspot.com/\" target=\"_blank\">Data source</a></p>')
    html.write('</section>')

    # load NOAA options
    NOAA_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-NOAA.json')
    METEOR_OPTIONS = wxcutils.load_json(CONFIG_PATH, 'config-METEOR.json')
    if NOAA_OPTIONS['tweet'] == 'yes' or METEOR_OPTIONS['tweet'] == 'yes':
        TWITTER_CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-twitter.json')
        html.write('<section class=\"content-section container\">')
        html.write('<h2 class=\"section-header\">Twitter Feed</h2>')
        html.write('<p>Tweeting images to <a href=\"https://twitter.com/' + TWITTER_CONFIG['tweet to'].replace('@', '') + '\">' + TWITTER_CONFIG['tweet to'] + '</a> for:</p><ul>')
        if NOAA_OPTIONS['tweet'] == 'yes':
            html.write('<li>NOAA - enhancement option = ' + NOAA_OPTIONS['tweet enhancement'] + '</li>')
        if METEOR_OPTIONS['tweet'] == 'yes':
            html.write('<li>METEOR - format option = ' + METEOR_OPTIONS['tweet image'] + '</li>')
        html.write('</ul></section>')

    html.write('<footer class=\"main-footer\">')
    html.write('<p id=\"footer-text\">Satellite Status last updated at <span class=\"time\">' +
               time.strftime('%H:%M (' +
                             subprocess.check_output("date").
                             decode('utf-8').split(' ')[-2] +
                             ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
               '.</p>')
    html.write('</footer>')
    html.write('</body></html>')

# acp file to destination
MY_LOGGER.debug('SCP files')
scp_files()

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
