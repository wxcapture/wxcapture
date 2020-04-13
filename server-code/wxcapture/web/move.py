#!/usr/bin/env python3
"""move files to web server directory"""

import os
from os import listdir
from os.path import isfile, join
import glob
import subprocess
import time
import fnmatch
from datetime import datetime
from dateutil import rrule

import wxcutils


def mk_dir(directory):
    """only create if it does not already exist"""
    MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


def find_files(directory, pattern):
    """find files that match the pattern"""
    for root, dirs, files in os.walk(directory):
        # MY_LOGGER.debug('find_files %s %s %s', root, dirs, files)
        for base_name in files:
            if fnmatch.fnmatch(base_name, pattern):
                filename = os.path.join(root, base_name)
                yield filename


def ordinal(num):
    """get the ordinalinal date description"""
    return str(num) + ("th" if 4 <= num % 100 <= 20 else
                       {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th"))


def files_to_copy(tmp_file_path, tmp_file_match, tmp_filename):
    """check for files matching in the passed directory"""
    # MY_LOGGER.debug('Is file the right type - %s %s', tmp_file_match, tmp_filename)
    if os.path.splitext(tmp_file_match)[1] == os.path.splitext(tmp_filename)[1]:
        MY_LOGGER.debug('File is of the correct type')
        MY_LOGGER.debug('Looking in %s for files like %s', tmp_file_path, tmp_file_match)
        if not glob.glob(tmp_file_path + tmp_file_match):
            MY_LOGGER.debug('No match exists')
            return False
        MY_LOGGER.debug('Match exists')
        return True
    MY_LOGGER.debug('File is of the incorrect type')
    return False


def make_directories(target, element0, element1, element2):
    """create directory structure"""
    MY_LOGGER.debug('Making directory structure %s %s %s %s',
                    target, element0, element1, element2)
    mk_dir(target + element0)
    mk_dir(target + element0 + '/' + element1)
    mk_dir(TARGET + element0 + '/' + element1 + '/' + element2)
    mk_dir(target + element0 + '/' + element1 + '/' + element2 + '/images')
    mk_dir(target + element0 + '/' + element1 + '/' + element2 + '/audio')


def get_links(tmp_date_start, tmp_date_now):
    """get a list of links to previous capture pages"""
    MY_LOGGER.debug('get_links')
    page_links = []
    for tmp_dt in rrule.rrule(rrule.MONTHLY, dtstart=tmp_date_start, until=tmp_date_now):
        tmp_month = tmp_dt.strftime('%m')
        tmp_month_name = tmp_dt.strftime('%B')
        tmp_year = tmp_dt.strftime('%Y')
        MY_LOGGER.debug('Year = %s Month = %s %s', tmp_year, tmp_month, tmp_month_name)
        link = '../../' + tmp_year + '/' + tmp_month + '/' + CAPTURES_PAGE
        MY_LOGGER.debug('link = %s ', link)
        page_links.append({'link': link, 'year': tmp_year, 'month': tmp_month,
                           'month name': tmp_month_name, 'sort order': tmp_year + tmp_month})
    MY_LOGGER.debug('page_links %s', page_links)

    page_links = sorted(page_links, key=lambda k: k['sort order'], reverse=True)
    MY_LOGGER.debug('page_links %s', page_links)

    result = '<ul>'
    current_year = ''
    link_count = 0
    for elem in page_links:
        if current_year != elem['year']:
            # new year
            link_count = 0
            if current_year != '':
                result = result[:len(result) - 4]
                result += '</ul>'
            current_year = elem['year']
            result += '<li>' + elem['year'] + '</li><ul><li>'
        result += '<a href=\"' + elem['link'] + '\"> -' + elem['month name'] + '- </a>'
        link_count += 1
        if link_count == 4:
            link_count = 0
            result += '</li><li>'
    if result[len(result) - 4:] == '<li>':
        result = result[:len(result) - 4]
    result += '</ul></ul>'
    MY_LOGGER.debug('result = %s', result)

    return result

def build_month_page(bpm_file_path, bpm_file_name, bpm_month, bpm_month_name, bpm_year):
    """build captures page for the month / year"""

    def write_month(tmp_file_path, tmp_dir, tmp_title):
        """write out the detail for the month"""
        data = ''
        # only do this if the directory exists
        if os.path.isdir(tmp_file_path + tmp_dir):
            MY_LOGGER.debug('Directory %s%s exists', tmp_file_path, tmp_dir)
            MY_LOGGER.debug('write_month %s %s %s', tmp_file_path, tmp_dir, tmp_title)
            filename_list = []
            for filename in find_files(tmp_file_path + tmp_dir, '*.html'):
                MY_LOGGER.debug('filename found = %s', filename)
                if CAPTURES_PAGE in filename:
                    MY_LOGGER.debug('Skipping existing %s file', CAPTURES_PAGE)
                else:
                    filename_list.append(filename)
            filename_list.sort(reverse=True)
            day = ''
            data += '<ul>'
            cp_html.write('<ul>')
            for filename in filename_list:
                new_day = filename.replace(tmp_file_path + tmp_dir, '')[0:2]
                if day != new_day:
                    if day != '':
                        cp_html.write('</ul>')
                        data += '</ul>'
                    day = new_day
                    MY_LOGGER.debug('filename = %s', filename)
                    pass_date = datetime. \
                        strptime(filename.replace(tmp_file_path + tmp_dir,
                                                  '')[3:13], '%Y-%m-%d')
                    cp_html.write('<li>' + pass_date.strftime('%a') + ' ' +
                                  ordinal(int(day)) + '</li><ul>')
                    data += '<li>' + pass_date.strftime('%a') + ' ' + \
                        ordinal(int(day)) + '</li><ul>'
                satellite = '???'
                if 'NOAA' in filename:
                    satellite = filename[61:68].replace('_', ' ')
                elif 'METEOR-M_2' in filename:
                    satellite = 'Meteor-M 2'
                elif 'METEOR-M2_2' in filename:
                    satellite = 'Meteor-M2 2'
                elif 'ISS_ZARYA' in filename:
                    satellite = 'ISS'
                elif 'SAUDISAT_1C_SO-50' in filename:
                    satellite = 'SAUDISAT-1C (SO-50)'

                utc_time = filename[52:60].replace('-', ':')
                utc_date = filename[30:40]
                local_date_time = wxcutils.epoch_to_local(wxcutils.utc_to_epoch(utc_time + ' ' + \
                                                 utc_date, '%H:%M:%S %Y/%m/%d'), \
                                                 '%H:%M:%S %a %d')
                cp_html.write('<li><a href="' + filename.replace(tmp_file_path, '')
                              + '">UTC ' + utc_time + ' (' + LOCAL_TIME_ZONE + ' ' +
                              local_date_time +
                              ') ' + satellite + '</a></li>')
                data += '<li><a href="' + filename.replace(tmp_file_path, '') + \
                    '">UTC ' + utc_time + ' (' + LOCAL_TIME_ZONE + ' ' + \
                    local_date_time + ') ' + satellite + '</a></li>'
            cp_html.write('</ul>')
            data += '</ul>'
        return data

    # now create captures page
    with open(bpm_file_path + bpm_file_name, 'w') as cp_html:
        # html header
        cp_label = bpm_month_name + ' ' + bpm_year
        cp_html.write('<!DOCTYPE html>')
        cp_html.write('<html lang=\"en\"><head><title>Captures ' + cp_label + '</title>'
                      '<link rel=\"stylesheet\" href=\"../../css/styles.css\">')
        cp_html.write('</head>')
        cp_html.write('<body>')
        cp_html.write(wxcutils.load_file(CONFIG_PATH,
                                         'main-header-2up.txt').replace('PAGE-TITLE', \
            'Weather Satellite Captures'))

        cp_html.write('<section class=\"content-section container\">')
        cp_html.write('<h2 class=\"section-header\">All Captures by Year and Month</h2>')
        cp_html.write(HISTORIC_LINKS)
        cp_html.write('</section>')

        cp_html.write('<section class=\"content-section container\">')
        cp_html.write('<h2 class=\"section-header\">' + cp_label + '</h2>')
        result = write_month(OUTPUT_PATH, '/wxcapture/' + bpm_year + '/' + bpm_month + '/',
                             bpm_month_name + ' ' + bpm_year)
        cp_html.write('</section>')
        cp_html.write('<footer class=\"main-footer\">')
        cp_html.write('<p>Captures last updated at ' +
                      time.strftime('%H:%M (' +
                                    subprocess.check_output("date").
                                    decode('utf-8').split(' ')[-2] +
                                    ') on the %d/%m/%Y') +
                      '.</p>')
        cp_html.write('</footer>')
        cp_html.write('</body></html>')

        return result

# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'move'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
# MY_LOGGER = wxcutils.get_logger(MODULE, FILE_PATH + 'logs/', MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')

MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# set up paths
MY_PATH = '/home/mike/wxcapture/output/'
TARGET = '/media/storage/html/wxcapture/'
OUTPUT_PATH = '/media/storage/html'
CAPTURES_PAGE = 'captures.html'

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]

MY_LOGGER.debug('Starting file moving')

# move satpass.html
if os.path.isfile(MY_PATH + 'satpass.html'):
    wxcutils.move_file(MY_PATH, 'satpass.html', TARGET, 'satpass.html')
else:
    MY_LOGGER.debug('No satpass.html to copy')

# move satellitestatus.html
if os.path.isfile(MY_PATH + 'satellitestatus.html'):
    wxcutils.move_file(MY_PATH, 'satellitestatus.html', TARGET, 'satellitestatus.html')
else:
    MY_LOGGER.debug('No satellitestatus.html to copy')

# move plot files
ONLY_FILES = [f for f in listdir(MY_PATH + 'images/') if isfile(join(MY_PATH + 'images/', f))]
MY_LOGGER.debug(ONLY_FILES)

for x in ONLY_FILES:
    MY_LOGGER.debug('x = %s', x)
    elements = x.split('-')
    make_directories(TARGET, elements[0], elements[1], elements[2])
    wxcutils.move_file(MY_PATH + 'images/', x,
                       TARGET + elements[0] + '/' +
                       elements[1] + '/' + elements[2] + '/images/', x)

# move remaining files, non-plot files, to right subdirectories
ONLY_FILES = [f for f in listdir(MY_PATH) if isfile(join(MY_PATH, f))]
ONLY_FILES.extend([f for f in listdir(MY_PATH + 'images/') if isfile(join(MY_PATH + 'images/', f))])
ONLY_FILES.extend([f for f in listdir(MY_PATH + 'audio/') if isfile(join(MY_PATH + 'audio/', f))])

if not ONLY_FILES:
    MY_LOGGER.debug('No other files to move')
else:
    for x in ONLY_FILES:
        MY_LOGGER.debug('x = %s', x)
        elements = x.split('-')
        make_directories(TARGET, elements[0], elements[1], elements[2])

        if files_to_copy(MY_PATH, '*.html', x):
            MY_LOGGER.debug('Moving html file(s)')
            wxcutils.move_file(MY_PATH, x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/', x)
        else:
            MY_LOGGER.debug('No html file(s) to move')
        if files_to_copy(MY_PATH, '*.json', x):
            MY_LOGGER.debug('Moving json file(s)')
            wxcutils.move_file(MY_PATH, x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/', x)
        else:
            MY_LOGGER.debug('No json file(s) to move')
        if files_to_copy(MY_PATH, '*.txt', x):
            MY_LOGGER.debug('Moving txt file(s)')
            wxcutils.move_file(MY_PATH, x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/', x)
        else:
            MY_LOGGER.debug('No txt file(s) to move')
        if files_to_copy(MY_PATH, '*.tle', x):
            MY_LOGGER.debug('Moving tle file(s)')
            wxcutils.move_file(MY_PATH, x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/', x)
        if files_to_copy(MY_PATH, '*.dec', x):
            MY_LOGGER.debug('Moving dec file(s)')
            wxcutils.move_file(MY_PATH, x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/', x)
        else:
            MY_LOGGER.debug('No dec file(s) to move')
        if files_to_copy(MY_PATH + 'audio/', '*.wav', x):
            MY_LOGGER.debug('Moving audio file(s)')
            wxcutils.move_file(MY_PATH + 'audio/', x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/audio/', x)
        else:
            MY_LOGGER.debug('No audio file(s) to move')
        if files_to_copy(MY_PATH + 'images/', '*.jpg', x):
            MY_LOGGER.debug('Moving image file(s)')
            wxcutils.move_file(MY_PATH + 'images/', x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/images/', x)
        else:
            MY_LOGGER.debug('No jpg file(s) to move')
        if files_to_copy(MY_PATH + 'images/', '*.png', x):
            MY_LOGGER.debug('Moving image file(s)')
            wxcutils.move_file(MY_PATH + 'images/', x, TARGET + elements[0] + '/' +
                               elements[1] + '/' + elements[2] + '/images/', x)
        else:
            MY_LOGGER.debug('No jpg file(s) to move')

MY_LOGGER.debug('Finished file moving')
MY_LOGGER.debug('Starting capture page building')


# find the start of time
MOVE_CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-move.json')
MY_LOGGER.debug('Start of time is %s %s', MOVE_CONFIG['Start Month'], MOVE_CONFIG['Start Year'])

DATE_START = datetime.strptime('01 ' + MOVE_CONFIG['Start Month'] + ' ' + \
    MOVE_CONFIG['Start Year'], '%d %m %Y')
DATE_NOW = datetime.now()

# get the historic links data to include in all pages
HISTORIC_LINKS = get_links(DATE_START, DATE_NOW)

# if between 1:00:00am and 1:01:59 - rebuild all previous content pages
# not perfectly efficient, but means that all pages have the link list for all
# months / years recorded after that month
HOURS = int(time.strftime('%H'))
MINUTES = int(time.strftime('%M'))

if (HOURS == 1) and (MINUTES in (0, 1)):
    # rebuilding all pages overnight
    MY_LOGGER.debug('Building pages for all mmonths / years overnight')
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=DATE_START, until=DATE_NOW):
        month = dt.strftime('%m')
        month_name = dt.strftime('%B')
        year = dt.strftime('%Y')
        file_path = OUTPUT_PATH + '/wxcapture/' + year + '/' + month + '/'
        MY_LOGGER.debug('Building captures page = %s for %s %s', file_path, month_name, year)
        page_data = build_month_page(file_path, CAPTURES_PAGE, month, month_name, year)

# rebuild the page for this month
# do this every time we run to get latest pass included
MONTH = DATE_NOW.strftime('%m')
MONTH_NAME = DATE_NOW.strftime('%B')
YEAR = DATE_NOW.strftime('%Y')
FILE_PATH = OUTPUT_PATH + '/wxcapture/' + YEAR + '/' + MONTH + '/'
MY_LOGGER.debug('Building captures page = %s for %s %s (current month)',
                FILE_PATH, MONTH_NAME, YEAR)
PAGE_DATA = build_month_page(FILE_PATH, CAPTURES_PAGE, MONTH, MONTH_NAME, YEAR)



# build current page which redirects to current month page

# MY_LOGGER.debug('Page data = %s', PAGE_DATA)
CURRENT_LINK = '/wxcapture/' + YEAR + '/' + MONTH + '/' + CAPTURES_PAGE
with open(TARGET + CAPTURES_PAGE, 'w') as html:
    # html header
    LABEL = MONTH_NAME + ' ' + YEAR
    html.write('<!DOCTYPE html>')
    html.write('<html lang=\"en\"><head><title>Captures</title>'
               '<link rel=\"stylesheet\" href=\"css/styles.css\">')
    html.write('<meta http-equiv = \"refresh\" content = \"0; url = ' + CURRENT_LINK + '\" />')
    html.write('</head>')
    html.write('<body>')
    html.write(wxcutils.load_file(CONFIG_PATH,
                                  'main-header.txt').replace('PAGE-TITLE',
                                                             'Weather Satellite Captures'))

    html.write('<section class=\"content-section container\">')
    html.write('<h2 class=\"section-header\">Redirect Page</h2>')
    html.write('<p>Your browser should be redirecting you to the page for the current month - ')
    html.write('<a href=\"' + CURRENT_LINK + '\">' + LABEL + '</a>.</p>')
    html.write('<p>Click the link if you have not been redirected.</p>')
    html.write('</section>')


    html.write('<footer class=\"main-footer\">')
    html.write('<p>Captures last updated at ' +
               time.strftime('%H:%M (' +
                             subprocess.check_output("date").
                             decode('utf-8').split(' ')[-2] +
                             ') on the %d/%m/%Y') +
               '.</p>')
    html.write('</footer>')
    html.write('</body></html>')

MY_LOGGER.debug('Finished capture page building')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
