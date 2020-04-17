#!/usr/bin/env python3
"""move files to web server directory"""


# import libraries
import os
from os import listdir
from os.path import isfile, join
import fnmatch
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


    def fix_img(fi_page):
        """fix up the img tags for lightbox"""
        MY_LOGGER.debug('starting fix_img')
        start_tag = '<a href=\"images/'
        mid_tag = '\"><img src=\"images/'
        end_tag = '\"></a>'
        parse_pos = 0
        new_page = ''
        img_path = '??????'
        while parse_pos >= 0:
            if fi_page.find(start_tag, parse_pos) > 0:

                first_pos_left = fi_page.find(start_tag, parse_pos) + len(start_tag)
                first_pos_right = fi_page.find(mid_tag, first_pos_left)
                second_pos_left = first_pos_right + len(mid_tag)
                second_pos_right = fi_page.find(end_tag, second_pos_left)

                main_img = fi_page[first_pos_left:first_pos_right]
                thumb_img = fi_page[second_pos_left:(second_pos_right)]
                bits = main_img[:10].split('-')
                
                img_path = '/wxcapture/' + bits[0] + '/' + bits[1] + '/' + bits[2] + '/images/'

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

    # create page backup file
    # only if there isn't an existing .backup file (i.e. our backup of the original)
    if not os.path.isfile(ff_path + ff_filename + '.backup'):
        MY_LOGGER.debug('no existing backup, so creating page backup file')
        wxcutils.run_cmd('cp ' + ff_path + ff_filename + ' ' + ff_path + ff_filename + '.backup')
    else:
         MY_LOGGER.debug('File backup exists, so retaining original backup')

    # load file
    MY_LOGGER.debug('load file')
    ff_page = wxcutils.load_file(ff_path, ff_filename)

    # add stylesheets
    MY_LOGGER.debug('add stylesheets')
    ff_page = update_page(ff_page, '</head>', '<link rel=\"stylesheet\" href=\"/wxcapture/css/styles.css\"><link rel=\"stylesheet\" href=\"/wxcapture/lightbox/css/lightbox.min.css\"></head>')

    # add script code
    MY_LOGGER.debug('add script code')
    ff_page = update_page(ff_page, '</body>', '<script src=\"/wxcapture/lightbox/js/lightbox-plus-jquery.min.js\"></script></body>')

    # remove table start
    MY_LOGGER.debug('remove table start')
    ff_page = update_page(ff_page, '</h2><table><tr><td>', '</h2>')

    # remove table end
    MY_LOGGER.debug('remove table end')
    ff_page = update_page(ff_page, '</td><td></table>', '<br>')

    # remove table border
    MY_LOGGER.debug('remove table border')
    ff_page = update_page(ff_page, '<table border = 1>', '<table>')

    # update img tags to use lightbox
    ff_page = fix_img(ff_page)
    
    # MY_LOGGER.debug('%s', ff_page)

    # save file
    wxcutils.save_file(ff_path, ff_filename, ff_page)


# setup paths to directories
HOME = '/home/mike'
APP_PATH = HOME + '/wxcapture/web/'
LOG_PATH = APP_PATH + 'logs/'
CONFIG_PATH = APP_PATH + 'config/'

# start logging
MODULE = 'fix_pass_pages'
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

MY_LOGGER.debug('Starting file fixing')

# find the files to skip, changing only those for satellite passes
for filename in find_files(TARGET, '*.html'):
    if 'NOAA' in filename or '.backup' in filename or 'METEOR' in filename or 'ISS' in filename or 'SAUDISAT' in filename:
        path_part, file_part = os.path.split(filename)
        MY_LOGGER.debug('Fixing - filename = %s, path = %s, file = %s', filename, path_part, file_part)
        fix_file(path_part + '/', file_part)
    else:
        MY_LOGGER.debug('SKIPing            = %s', filename)


MY_LOGGER.debug('Finished file fixing')

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
