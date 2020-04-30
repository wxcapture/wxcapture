#!/usr/bin/env python3
"""move files to web server directory"""


# import libraries
import os
from os import listdir
from os.path import isfile, join
import glob
import sys
import subprocess
import time
import fnmatch
from datetime import datetime
from dateutil import rrule
import wxcutils
import fix_pass_pages_lib


def mk_dir(directory):
    """only create if it does not already exist"""
    MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


def find_files(directory, pattern):
    """find files that match the pattern"""
    for root, dirs, files in os.walk(directory):
        MY_LOGGER.debug('find_files %s %s %s', root, dirs, files)
        for base_name in files:
            if fnmatch.fnmatch(base_name, pattern):
                filename = os.path.join(root, base_name)
                yield filename


def build_pass_json():
    """build json file for all passes"""
    MY_LOGGER.debug('building pass json')
    json_data = []
    for filename in find_files(TARGET, '*.html'):
        if not ('index.html' in filename or 'captures.html' in filename or 'resources.html' in filename or 'satellitestatus.html' in filename or 'satpass.html' in filename or 'meteor_index.html' in filename or 'meteor.html' in filename):
            # MY_LOGGER.debug('found pass page - filename = %s', filename)
            bpj_file_path, html_file = os.path.split(filename)
            base_filename, base_extension = os.path.splitext(html_file)
            filename_root = filename[:len(filename) - len(base_extension)]
            # look for all the image files and add to the list
            # to avoid the json file getting too large, extract the enhancement part only
            image_files = glob.glob(bpj_file_path + '/images/' + base_filename + '*.jpg')
            image_enhancements = []
            for entry in image_files:
                if entry[len(entry) - 7:] != '-tn.jpg':
                    result = entry.replace('.jpg', '').replace(bpj_file_path + '/images/', '').replace(base_filename, '')
                    image_enhancements.append(result[1:])

            json_data.append({'path': filename_root.replace(OUTPUT_PATH, ''),
                              'enhancement': image_enhancements
                             })
    MY_LOGGER.debug('saving passses.json')
    wxcutils.save_json(TARGET, 'passes.json', json_data)


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
                elif 'index.html'  in filename:
                    MY_LOGGER.debug('Skipping existing index.html file')
                else:
                    filename_list.append(filename)
            filename_list.sort(reverse=True)
            day = ''
            data += '<ul>'
            cp_html.write('<ul>')
            for filename in filename_list:
                if 'meteor.html' in filename:
                    MY_LOGGER.debug('Skipping meteor.html page')
                else:
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
                    MY_LOGGER.debug('finding satellite name for %s', filename)
                    for sat_test in SAT_DATA:
                        if sat_test['code'] in filename:
                            satellite = sat_test['name']

                    utc_time = filename[52:60].replace('-', ':')
                    utc_date = filename[30:40]
                    local_date_time = wxcutils.epoch_to_local(wxcutils.utc_to_epoch(utc_time + ' ' + \
                                                    utc_date, '%H:%M:%S %Y/%m/%d'), \
                                                    '%H:%M:%S %a %d')
                    cp_html.write('<li><a href="' + filename.replace(tmp_file_path, '')
                                  + '" rel=\"modal:open\">UTC ' + utc_time + ' (' + LOCAL_TIME_ZONE + ' ' +
                                  local_date_time +
                                  ') ' + satellite + '</a></li>')
                    data += '<li><a href="' + filename.replace(tmp_file_path, '') + \
                        '">UTC ' + utc_time + ' (' + LOCAL_TIME_ZONE + ' ' + \
                        local_date_time + ') ' + satellite + '</a></li>'
            cp_html.write('</ul>')
            data += '</ul>'
        return data

    MY_LOGGER.debug('build_month_page for %s %s %s %s %s', bpm_file_path, bpm_file_name,
                    bpm_month, bpm_month_name, bpm_year)
    # now create captures page
    with open(bpm_file_path + bpm_file_name, 'w') as cp_html:
        # html header
        cp_label = bpm_month_name + ' ' + bpm_year
        cp_html.write('<!DOCTYPE html>')
        cp_html.write('<html lang=\"en\"><head>'
                      '<meta charset=\"UTF-8\">'
                      '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                      '<meta name=\"description\" content=\"xyzzy\">'
                      '<meta name=\"keywords\" content=\"wxcapture, weather, satellite, NOAA, Meteor, images, ISS, Zarya, SSTV, Amsat, orbit, APT, LRPT, SDR, Mike, KiwiinNZ, Albert, Technobird22, Predictions, Auckland, New Zealand, storm, cyclone, hurricane, front, rain, wind, cloud\">'
                      '<meta name=\"author\" content=\"WxCapture\">'
                      '<title>Captures ' + cp_label + '</title>'
                      '<link rel=\"stylesheet\" href=\"../../css/styles.css\">'
                      '<link rel=\"shortcut icon\" type=\"image/png\" href=\"/wxcapture/favicon.png\"/>'
                      '<script src=\"https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js\"></script>'
                      '<script src=\"../../js/jquery.modal.min.js\"></script>'
                      '<link rel=\"stylesheet\" href=\"../../css/jquery.modal.min.css\" />')
        cp_html.write('</head>')
        cp_html.write('<body onload=\"defaulthide()\">')
        cp_html.write(wxcutils.load_file(CONFIG_PATH,
                                         'main-header-2up.txt').replace('PAGE-TITLE', \
            'Satellite Captures'))

        cp_html.write('<section class=\"content-section container\">')

        cp_html.write('<button onclick=\"hideshowinstructions()\" id=\"showhideinstructions\" class=\"showhidebutton\">Show instructions</button>')
        cp_html.write('&nbsp;')
        cp_html.write('<button onclick=\"hideshowlinks()\" id=\"showhidelinks\" class=\"showhidebutton\">Show previous months / years</button>')

        cp_html.write('<div id=\"instructionsDiv\">')
        cp_html.write('<h2 class=\"section-header\">Instructions</h2>')
        cp_html.write('<ul>')
        cp_html.write('<li>Click on any pass to see the full pass information including the images</li>')
        cp_html.write('<li>If you click outside the pop up or on the X and you\'ll return to the pass list</li>')
        cp_html.write('<li>Or click on an image and you\'ll see the image in full detail</li>')
        cp_html.write('<li>If you click outside the pop up window or on the X and you\'ll return to the pass information</li>')
        cp_html.write('</ul>')
        cp_html.write('</div>')

        cp_html.write('<div id=\"linksDiv\">')
        cp_html.write('<h2 class=\"section-header\">All Captures by Year and Month</h2>')
        cp_html.write(HISTORIC_LINKS)
        cp_html.write('</div>')

        cp_html.write('</section>')

        cp_html.write('<section class=\"content-section container\">')
        cp_html.write('<h2 class=\"section-header\">' + cp_label + '</h2>')
        result = write_month(OUTPUT_PATH, '/wxcapture/' + bpm_year + '/' + bpm_month + '/',
                             bpm_month_name + ' ' + bpm_year)
        cp_html.write('</ul></section>')
        cp_html.write('<footer class=\"main-footer\">')
        cp_html.write('<p id=\"footer-text\">Captures last updated at <span class=\"time\">' +
                      time.strftime('%H:%M (' +
                                    subprocess.check_output("date").
                                    decode('utf-8').split(' ')[-2] +
                                    ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
                      '.</p>')
        cp_html.write('</footer>')

        cp_html.write('<script>')
        cp_html.write('function hideshowlinks() {')
        cp_html.write('  var x = document.getElementById(\"linksDiv\");')
        cp_html.write('  if (x.style.display === \"none\") {')
        cp_html.write('   x.style.display = \"block\";')
        cp_html.write('   showhidelinks.innerHTML = \"Hide previous months / years\";')
        cp_html.write(' } else {')
        cp_html.write('   x.style.display = \"none\";')
        cp_html.write('   showhidelinks.innerHTML = \"Show previous months / years\";')
        cp_html.write(' }')
        cp_html.write('}')
        cp_html.write('function hideshowinstructions() {')
        cp_html.write('  var x = document.getElementById(\"instructionsDiv\");')
        cp_html.write('  if (x.style.display === \"none\") {')
        cp_html.write('    x.style.display = \"block\";')
        cp_html.write('    showhideinstructions.innerHTML = \"Hide instructions\";')
        cp_html.write(' } else {')
        cp_html.write('   x.style.display = \"none\";')
        cp_html.write('   showhideinstructions.innerHTML = \"Show instructions\";')
        cp_html.write(' }')
        cp_html.write('}')
        cp_html.write('function defaulthide() {')
        cp_html.write('  var x = document.getElementById(\"linksDiv\");')
        cp_html.write('  x.style.display = \"none\";')
        cp_html.write('  showhidelinks.innerHTML = \"Show previous months / years\";')
        cp_html.write('  var y = document.getElementById(\"instructionsDiv\");')
        cp_html.write('  y.style.display = \"none\";')
        cp_html.write('  showhideinstructions.innerHTML = \"Show instructions\";')
        cp_html.write('}')
        cp_html.write('</script>')

        cp_html.write('</body></html>')

        return result


def process_file(pf_path_filename, pf_source_path, pf_target_path, pf_target_suffix, pf_lock_suffix):
    """process file, copying it to the correct directory"""
    MY_LOGGER.debug('process file %s %s %s %s %s', pf_path_filename, pf_source_path, pf_target_path, pf_target_suffix, pf_lock_suffix)
    pf_filename_lock = pf_path_filename.split(pf_source_path)[1]
    pf_filename = pf_filename_lock.split(pf_lock_suffix)[0]
    pf_directory_elements = pf_filename.split('-')
    MY_LOGGER.debug('filename = %s', pf_filename)
    # create directory structure
    make_directories(pf_target_path, pf_directory_elements[0], pf_directory_elements[1], pf_directory_elements[2])
    # move file
    pf_move_to_path = pf_target_path + pf_directory_elements[0] + '/' + pf_directory_elements[1] + '/' + pf_directory_elements[2] + '/' + pf_target_suffix
    MY_LOGGER.debug('Moving %s %s to %s %s', pf_source_path, pf_filename + pf_lock_suffix, pf_move_to_path, pf_filename)
    wxcutils.move_file(pf_source_path, pf_filename + pf_lock_suffix, pf_move_to_path, pf_filename)
    # remove any existing .html.backup file as this will prevent files being reprocessed
    # as the existing .html.backup file will be used instead of the new .html file which
    # will be overwritten
    if '.html' in pf_filename:
        MY_LOGGER.debug('Deleting old .html.backup file')
        wxcutils.run_cmd('rm ' + pf_move_to_path + '/' + pf_filename + '.backup')


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'move_modal'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
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

try:
    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]

    # load satellites
    SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'satellites.json')

    SAT_DATA = []
    for key, value in SATELLITE_INFO.items():
        for sat in SATELLITE_INFO[key]:
            SAT_DATA.append({'code': sat['name'].replace(' ', '_').replace('(', '').replace(')', ''), 'name': sat['name']})

    MY_LOGGER.debug('Starting file moving')

    # scan for any unlock files
    for unlock_file in glob.glob(MY_PATH + '*.UNLOCK'):
        unlock_path, unlock_filename = os.path.split(unlock_file)
        lock_number = unlock_filename.split('.')[0]
        lock_suffix = '.LOCK.' + lock_number
        MY_LOGGER.debug('Unlock file for %s %s - lock # %s lock suffix %s', unlock_path, unlock_filename, lock_number, lock_suffix)

        # move satpass.html
        if os.path.isfile(MY_PATH + 'satpass.html' + lock_suffix):
            wxcutils.move_file(MY_PATH, 'satpass.html' + lock_suffix, TARGET, 'satpass.html')
        else:
            MY_LOGGER.debug('No satpass.html to copy')

        # move satellitestatus.html
        if os.path.isfile(MY_PATH + 'satellitestatus.html' + lock_suffix):
            wxcutils.move_file(MY_PATH, 'satellitestatus.html' + lock_suffix, TARGET, 'satellitestatus.html')
        else:
            MY_LOGGER.debug('No satellitestatus.html to copy')

        # find images in the images folder and move them
        # will include plots, maps and sat images
        # .png and .jpg extensions
        MY_LOGGER.debug('Image search = %s', MY_PATH + 'images/*' + lock_suffix)
        for image_file in glob.glob(MY_PATH + 'images/*' + lock_suffix):
            MY_LOGGER.debug('Image file = %s', image_file)
            process_file(image_file, MY_PATH + 'images/', TARGET, 'images/', lock_suffix)

        # find audio files in the audio folder and move them
        # should be just .wav files
        MY_LOGGER.debug('Audio search = %s', MY_PATH + 'audio/*' + lock_suffix)
        for audio_file in glob.glob(MY_PATH + 'audio/*' + lock_suffix):
            MY_LOGGER.debug('Audio file = %s', audio_file)
            process_file(audio_file, MY_PATH + 'audio/', TARGET, 'audio/', lock_suffix)

        # find .tle files in the output folder and move them
        MY_LOGGER.debug('.tle search = %s', MY_PATH + '*.tle' + lock_suffix)
        for tle_file in glob.glob(MY_PATH + '*.tle' + lock_suffix):
            MY_LOGGER.debug('.tle file = %s', tle_file)
            process_file(tle_file, MY_PATH, TARGET, '', lock_suffix)

        # find .json files in the output folder and move them
        MY_LOGGER.debug('.json search = %s', MY_PATH + '*.json' + lock_suffix)
        for json_file in glob.glob(MY_PATH + '*.json' + lock_suffix):
            MY_LOGGER.debug('.json file = %s', json_file)
            process_file(json_file, MY_PATH, TARGET, '', lock_suffix)

        # find .txt files in the output folder and move them
        MY_LOGGER.debug('.txt search = %s', MY_PATH + '*.txt' + lock_suffix)
        for txt_file in glob.glob(MY_PATH + '*.txt' + lock_suffix):
            MY_LOGGER.debug('.txt file = %s', txt_file)
            process_file(txt_file, MY_PATH, TARGET, '', lock_suffix)

        # get a list of the pass html files for fixing
        PASS_FILES = [f for f in listdir(MY_PATH) if isfile(join(MY_PATH, f)) and '.UNLOCK' not in f]
        MY_LOGGER.debug('________________%s', PASS_FILES)

        # find .html files in the output folder and move them
        MY_LOGGER.debug('.html search = %s', MY_PATH + '*.html' + lock_suffix)
        for htm_file in glob.glob(MY_PATH + '*.html' + lock_suffix):
            MY_LOGGER.debug('.html file = %s', htm_file)
            process_file(htm_file, MY_PATH, TARGET, '', lock_suffix)

        # copying done for this lock, so remove unlock file
        wxcutils.run_cmd('rm ' + unlock_file)

        # apply the modal windows fix for all new pass html files
        for file_name in PASS_FILES:
            MY_LOGGER.debug('Applying modal fixes to pass files just copied')
            MY_LOGGER.debug('file_name = %s', file_name.split('.LOCK.')[0])
            file_bits = file_name.split('.LOCK.')[0].split('-')
            location = TARGET + file_bits[0] + '/' + file_bits[1] + '/' + file_bits[2] + '/'
            if '.html' in file_name:
                MY_LOGGER.debug('fix file %s %s', location, file_name.split('.LOCK.')[0])
                fix_pass_pages_lib.fix_file(location, file_name.split('.LOCK.')[0])


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
        html.write('<html lang=\"en\"><head>'
                   '<meta charset=\"UTF-8\">'
                   '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                   '<meta name=\"description\" content=\"WxCapture redirection page to current captures plus historic monthly / yearly captures\">'
                   '<meta name=\"keywords\" content=\"wxcapture, weather, satellite, NOAA, Meteor, images, ISS, Zarya, SSTV, Amsat, orbit, APT, LRPT, SDR, Mike, KiwiinNZ, Albert, Technobird22, Predictions, Auckland, New Zealand, storm, cyclone, hurricane, front, rain, wind, cloud\">'
                   '<meta name=\"author\" content=\"WxCapture\">'
                   '<title>Captures</title>'
                   '<link rel=\"stylesheet\" href=\"css/styles.css\">'
                   '<link rel=\"shortcut icon\" type=\"image/png\" href=\"/wxcapture/favicon.png\"/>')
        html.write('<meta http-equiv = \"refresh\" content=\"0; url=\'' + CURRENT_LINK + '\'\" />')
        html.write('</head>')
        html.write('<body>')
        html.write('<section class=\"content-section container\">')
        html.write('<h2 class=\"section-header\">Redirect Page</h2>')
        html.write('<p>Your browser should be redirecting you to the page for the current month - ')
        html.write('<a href=\"' + CURRENT_LINK + '\">' + LABEL + '</a>.</p>')
        html.write('<p>Click the link if you have not been redirected.</p>')
        html.write('</section>')

        html.write('</body></html>')

    MY_LOGGER.debug('Finished capture page building')

    MY_LOGGER.debug('Build json passes file')
    build_pass_json()
    MY_LOGGER.debug('Finished json passes file')
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
