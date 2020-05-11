#!/usr/bin/env python3
"""move files to web server directory"""


# import libraries
import os
import fnmatch
import logging
import wxcutils


def find_files(directory, pattern):
    """find files that match the pattern"""
    for root, dirs, files in os.walk(directory):
        # MY_LOGGER.debug('find_files %s %s %s', root, dirs, files)
        for base_name in files:
            if fnmatch.fnmatch(base_name, pattern):
                filename = os.path.join(root, base_name)
                yield filename


def fix_file(ff_path, ff_filename):
    """fix file for upgrade"""
    def update_page(up_page, up_search, up_replace):
        """update text file with search / replace"""
        MY_LOGGER.debug('%s %s', up_search, up_replace)
        if up_search in up_page:
            MY_LOGGER.debug('%s found', up_search)
            ff_location = up_page.find(up_search)
            if ff_location > 0:
                MY_LOGGER.debug('string found at %d', ff_location)
                # up_page.replace(up_search, up_replace, 1)
                left = up_page[0:ff_location]
                skip = ff_location + len(up_search)
                right = up_page[skip:]
                up_page = left + up_replace + right
            else:
                MY_LOGGER.debug('string NOT found')
        else:
            MY_LOGGER.debug('%s NOT found', up_search)
        # MY_LOGGER.debug('%s', up_page)
        return up_page


    def fix_img(fi_page, fi_path, fi_filename):
        """fix up the img tags for lightbox"""
        MY_LOGGER.debug('starting fix_img %s %s', fi_path, fi_filename)
        start_tag = '<a href=\"images/'
        mid_tag = '\"><img src=\"images/'
        end_tag = '\"></a>'
        parse_pos = 0
        new_page = ''

        img_pos = fi_path.find('/wxcapture/')
        img_path = fi_path[img_pos:] + 'images/'
        MY_LOGGER.debug('img_path = %s', img_path)

        while parse_pos >= 0:
            if fi_page.find(start_tag, parse_pos) > 0:

                first_pos_left = fi_page.find(start_tag, parse_pos) + len(start_tag)
                first_pos_right = fi_page.find(mid_tag, first_pos_left)
                second_pos_left = first_pos_right + len(mid_tag)
                second_pos_right = fi_page.find(end_tag, second_pos_left)

                main_img = fi_page[first_pos_left:first_pos_right]
                thumb_img = fi_page[second_pos_left:(second_pos_right)]
                bits = main_img[:10].split('-')

                img_path = CONFIG_INFO['Link Base'] + bits[0] + '/' + bits[1] + '/' + bits[2] + '/images/'

                MY_LOGGER.debug('%d %s %s %s', parse_pos, main_img, thumb_img, img_path)

                new_bit_1 = fi_page[parse_pos:(first_pos_left - len(start_tag))]
                new_bit_2 = '<a class=\"example-image-link\" href=\"' + img_path + \
                     main_img+ \
                    '\" data-lightbox=\"' + img_path + main_img + \
                    '\"><img class=\"example-image\" src=\"' + img_path + \
                    thumb_img + '"></a>'

                MY_LOGGER.debug('-start-----------------')
                MY_LOGGER.debug(new_page)
                MY_LOGGER.debug('-new_bit_1-------------')
                MY_LOGGER.debug(new_bit_1)
                MY_LOGGER.debug('-new_bit_2-------------')
                MY_LOGGER.debug(new_bit_2)
                MY_LOGGER.debug('-end-------------------')
                new_page += new_bit_1 + new_bit_2
                parse_pos = second_pos_right + len(end_tag)
            else:
                # get the rest of the page
                new_page += fi_page[parse_pos:]
                parse_pos = -1
        MY_LOGGER.debug('completed fix_img')

        # fix plot reference
        MY_LOGGER.debug('fix plot reference')
        new_page = update_page(new_page, '<img src=\"images/', '<img src=\"' + img_path)

        return new_page


    MY_LOGGER.debug('fix_file %s %s', ff_path, ff_filename)

    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    # create page backup file
    # only if there isn't an existing .backup file (i.e. our backup of the original)
    if not os.path.isfile(ff_path + ff_filename + '.backup'):
        MY_LOGGER.debug('no existing backup, so creating page backup file')
        wxcutils.copy_file(ff_path + ff_filename, ff_path + ff_filename + '.backup')
    else:
        MY_LOGGER.debug('File backup exists, so retaining original backup')
        # restore the backup and re-fix it
        wxcutils.copy_file(ff_path + ff_filename + '.backup', ff_path + ff_filename)

     # load file
    MY_LOGGER.debug('load file')
    ff_page = wxcutils.load_file(ff_path, ff_filename)

    # add stylesheets
    MY_LOGGER.debug('add stylesheets')
    ff_page = update_page(ff_page, '</head>', '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><meta name=\"description\" content=\"Satellite pass capture page for NOAA / Meteor / International Space Station (ISS) SSTV / Amsat (Amateur Satellites)\"><meta name=\"keywords\" content=\"wxcapture, weather, satellite, NOAA, Meteor, images, ISS, Zarya, SSTV, Amsat, orbit, APT, LRPT, SDR, Mike, KiwiinNZ, Albert, Technobird22, Predictions, Auckland, New Zealand, storm, cyclone, hurricane, front, rain, wind, cloud\"><meta name=\"author\" content=\"WxCapture\"><link rel=\"stylesheet\" href=\"/css/styles.css\"><link rel=\"stylesheet\" href=\"/lightbox/css/lightbox.min.css\"></head>')

    # add script code
    MY_LOGGER.debug('add script code')
    ff_page = update_page(ff_page, '</body>', '<script src=\"/lightbox/js/lightbox-plus-jquery.min.js\"></script></body>')

    # remove table start
    MY_LOGGER.debug('remove table start')
    ff_page = update_page(ff_page, '</h2><table><tr><td>', '</h2>')

    # remove table end
    MY_LOGGER.debug('remove table end')
    ff_page = update_page(ff_page, '</td><td></table>', '<br>')

    # remove table border
    MY_LOGGER.debug('remove table border')
    ff_page = update_page(ff_page, '<table border = 1>', '<table>')

    # fix audio link - amsat and ISS only
    if 'ISS' in ff_filename or 'SSTV' in ff_filename or 'SAUDISAT' in ff_filename or 'FOX' in ff_filename:
        audio_pos = ff_path.find('/wxcapture/')
        audio_path = ff_path[audio_pos:] + 'audio/'
        MY_LOGGER.debug('audio_path = %s', audio_path)
        ff_page = update_page(ff_page, '<a href=\"audio', '<a href=\"' + audio_path)

    # update img tags to use lightbox
    ff_page = fix_img(ff_page, ff_path, ff_filename)

    # MY_LOGGER.debug('%s', ff_page)

    # save file
    wxcutils.save_file(ff_path, ff_filename, ff_page)

FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
MY_LOGGER = None

# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'fix_pass_pages_lib'
MY_LOGGER = wxcutils.get_logger(MODULE, LOG_PATH, MODULE + '.log')
