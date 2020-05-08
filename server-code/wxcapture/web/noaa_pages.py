#!/usr/bin/env python3
"""create monthly page for noaa images"""


# import libraries
import os
import sys
import time
import calendar
import subprocess
import wxcutils
import fix_pass_pages_lib


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'noaa_pages'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
MY_LOGGER.debug('Execution start')

MY_LOGGER.debug('APP_PATH = %s', APP_PATH)
MY_LOGGER.debug('LOG_PATH = %s', LOG_PATH)
MY_LOGGER.debug('CONFIG_PATH = %s', CONFIG_PATH)

# set up paths
MY_PATH = '/home/mike/wxcapture/output/'
MY_LOGGER.debug('MY_PATH = %s', MY_PATH)


MY_LOGGER.debug('Starting file creation')

try:
    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    TARGET = CONFIG_INFO['web doc root location']
    MY_LOGGER.debug('TARGET = %s', TARGET)

    # find the files to skip, changing only those for satellite passes
    INDEX = []
    for filename in fix_pass_pages_lib.find_files(TARGET, 'captures.html'):
        if filename != TARGET + 'captures.html':
            noaa_filename = filename.replace('captures.html', 'noaa.html').replace(TARGET, '')
            bits = noaa_filename.split('/')
            year = bits[0]
            month = bits[1]
            MY_LOGGER.debug('Filename = %s, noaa_filename = %s, month = %s, year = %s', filename, noaa_filename, month, year)
            images_found = 0

            # now create captures page
            with open(TARGET + noaa_filename, 'w') as cp_html:
                # html header
                cp_label = 'NOAA Captures ' + calendar.month_name[int(month)] + ' - ' + year
                cp_html.write('<!DOCTYPE html>')
                cp_html.write('<html lang=\"en\"><head>'
                              '<meta charset=\"UTF-8\">'
                              '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                              '<meta name=\"description\" content=\"Monthly captures page for NOAA satellites\">'
                              '<meta name=\"keywords\" content=\"wxcapture, weather, satellite, NOAA, Meteor, images, ISS, Zarya, SSTV, Amsat, orbit, APT, LRPT, SDR, Mike, KiwiinNZ, Albert, Technobird22, Predictions, Auckland, New Zealand, storm, cyclone, hurricane, front, rain, wind, cloud\">'
                              '<meta name=\"author\" content=\"WxCapture\">'
                              '<title>' + cp_label + '</title>'
                              '<link rel=\"stylesheet\" href=\"../../css/styles.css\">'
                              '<link rel=\"shortcut icon\" type=\"image/png\" href=\"' + CONFIG_INFO['Link Base'] + 'favicon.png\"/>'
                              '<script src=\"https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js\"></script>')
                cp_html.write('</head>')
                cp_html.write('<body>')
                cp_html.write(wxcutils.load_file(CONFIG_PATH,
                                                 'main-header-2up.txt').replace('PAGE-TITLE', cp_label))

                cp_html.write('<section class=\"content-section container\">')

                cp_html.write('<h2 class=\"section-header\">' + cp_label + '</h2>')

                for filename_row in fix_pass_pages_lib.find_files(TARGET + year + '/' + month + '/', '*-norm-tn.jpg'):
                    if os.path.getsize(filename_row) > 3000:
                        images_found += 1
                        web_filename = filename_row.split(TARGET)[1]
                        path_part, file_part = os.path.split(web_filename)
                        MY_LOGGER.debug('Filename = %s, path = %s, file = %s',
                                        web_filename, path_part, file_part)
                        cp_html.write('<a href=\"' + CONFIG_INFO['Link Base'] + web_filename.replace('-tn', '') + '\">' + '<img src=\"' + CONFIG_INFO['Link Base'] + web_filename + '\"></a>')
                if images_found > 0:
                    INDEX.append({'month': month, 'year': year, 'date': year + month, 'page': noaa_filename})
                cp_html.write('</section>')

                cp_html.write('<footer class=\"main-footer\">')
                cp_html.write('<p id=\"footer-text\">Captures last updated at <span class=\"time\">' +
                              time.strftime('%H:%M (' +
                                            subprocess.check_output("date").
                                            decode('utf-8').split(' ')[-2] +
                                            ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
                              '.</p>')
                cp_html.write('</footer>')

                cp_html.write('</body></html>')


    # sort data
    MY_LOGGER.debug('Sort pages')
    INDEX = sorted(INDEX, key=lambda k: k['date'])

    # now create captures page
    with open(TARGET + 'noaa_index.html', 'w') as cp_html:
        # html header
        CP_LABEL = 'NOAA Captures Index'
        cp_html.write('<!DOCTYPE html>')
        cp_html.write('<html lang=\"en\"><head>'
                      '<meta charset=\"UTF-8\">'
                      '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                      '<meta name=\"description\" content=\"Monthly captures page for NOAA satellites\">'
                      '<meta name=\"keywords\" content=\"' + CONFIG_INFO['webpage keywords'] + '\">'
                      '<meta name=\"author\" content=\"WxCapture\">'
                      '<title>' + CP_LABEL + '</title>'
                      '<link rel=\"stylesheet\" href=\"css/styles.css\">'
                      '<link rel=\"shortcut icon\" type=\"image/png\" href=\"' + CONFIG_INFO['Link Base'] + 'favicon.png\"/>'
                      '<script src=\"https://ajax.googleapis.com/ajax/libs/jquery/3.4.1/jquery.min.js\"></script>')
        cp_html.write('</head>')
        cp_html.write('<body>')
        cp_html.write(wxcutils.load_file(CONFIG_PATH,
                                         'main-header.txt').replace('PAGE-TITLE', CP_LABEL))

        cp_html.write('<section class=\"content-section container\">')

        cp_html.write('<h2 class=\"section-header\">' + CP_LABEL + '</h2>')
        cp_html.write('<ul>')


        for pass_info in INDEX:
            MY_LOGGER.debug(pass_info)
            cp_html.write('<li><a href=\"' + pass_info['page'] + '\">' + calendar.month_name[int(pass_info['month'])] + ' - ' + pass_info['year'] + '</a></li>')

        cp_html.write('</ul>')
        cp_html.write('</section>')

        cp_html.write('<footer class=\"main-footer\">')
        cp_html.write('<p id=\"footer-text\">Captures last updated at <span class=\"time\">' +
                      time.strftime('%H:%M (' +
                                    subprocess.check_output("date").
                                    decode('utf-8').split(' ')[-2] +
                                    ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
                      '.</p>')
        cp_html.write('</footer>')

        cp_html.write('</body></html>')


    MY_LOGGER.debug('Finished file fixing')
except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
