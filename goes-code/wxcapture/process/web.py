#!/usr/bin/env python3
"""sync web satellite data"""


# import libraries
from genericpath import exists
import os
import sys
import time
import datetime
import requests
import subprocess
import calendar
import cv2
from bs4 import BeautifulSoup
import wxcutils


def listFD(url, ext=''):
    page = requests.get(url).text
    # print(page)
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]


def mk_dir(directory):
    """only create if it does not already exist"""
    # MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        MY_LOGGER.debug('Making directory %s', directory)
        wxcutils.make_directory(directory)


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %Y %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %Y %H:%M')


def get_last_generated_text(lgt_filename):
    """build the last generated text"""
    last_generated_text = 'Last generated at ' + get_local_date_time() + ' ' + \
                            LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    MY_LOGGER.debug('last_generated_text = %s - for file %s', last_generated_text, lgt_filename)
    return last_generated_text


def create_branded(cb_sat_type, cb_sat, cb_type, cb_channel, cb_dir, cb_file, cb_extension, cb_date, cb_time):
    """Create branded file"""

    def add_kiwiweather():
        """add kiwiweather"""
        # Kiwiweather.com
        nonlocal image
        image = cv2.putText(image, 'Kiwi', (xborder, yborder + y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            2, cv2.LINE_AA)
        image = cv2.putText(image, 'Weather', (xborder, yborder + (y_offset * 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            2, cv2.LINE_AA)
        image = cv2.putText(image, '.com', (xborder, yborder + (y_offset * 3)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            2, cv2.LINE_AA)
        image = cv2.putText(image, 'ZL4MDE', (xborder, yborder + (y_offset * 4)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size - 0,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            2, cv2.LINE_AA)

        if channel['logo'] == 'white':
            logo = LOGOWHITE
        else:
            logo = LOGOBLACK

        MY_LOGGER.debug('image x = %d, y = %d', image.shape[1], image.shape[0])
        MY_LOGGER.debug('logo x = %d, y = %d', logo.shape[1], logo.shape[0])
        x_offset = xborder
        MY_LOGGER.debug('%d, %d - %d, %d',
                        0,
                        logo.shape[0],
                        x_offset,
                        x_offset+logo.shape[1])

        # need to scale logo to match image size
        scaler = (image.shape[1] / 2700)
        new_x = int(logo.shape[1] * scaler)
        new_y = int(logo.shape[0] * scaler)
        MY_LOGGER.debug('scaler = %d, new x = %d, new_y = %d', scaler, new_x, new_y)
        scaled_image = cv2.resize(logo, (new_x, new_y), interpolation=cv2.INTER_AREA)

        image[yborder+(y_offset * 4):yborder+scaled_image.shape[0]+(y_offset * 4), x_offset:x_offset+scaled_image.shape[1]] = scaled_image


    def add_acknowledgement():
        """add acknowledgement"""
        nonlocal image
        # add acknowledgement?
        MY_LOGGER.debug('adding acknowledgement %s, %s', sat['acknowledge1'], sat['acknowledge2'])
        x_offset = int(image.shape[1] * .8)
        MY_LOGGER.debug('x_offset = %d, y_offset = %d, yborder = %d, font_size = %d', x_offset, y_offset, yborder, font_size)
        image = cv2.putText(image, sat['acknowledge1'], (x_offset, yborder + (y_offset * 1)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)
        image = cv2.putText(image, sat['acknowledge2'], (x_offset, yborder + (y_offset * 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size - 2,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)


    def add_date(ad_date, ad_time):
        """add date and time"""
        MY_LOGGER.debug('date = %s, time = %s', ad_date, ad_time)
        MY_LOGGER.debug('y_offset = %d, yborder = %d, font_size = %d', y_offset, yborder, font_size)
        nonlocal image
        image = cv2.putText(image, ad_time, (xborder, image.shape[0] - yborder - y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)
        image = cv2.putText(image, ad_date, (xborder, image.shape[0] - yborder),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)


    def add_sat_info():
        """add satellite info"""
        MY_LOGGER.debug('sat = %s, channel = %s', sat['desc'], channel['desc'])
        nonlocal image
        MY_LOGGER.debug('%d, %d, %d', image.shape[1], (80 * len(channel['desc'])), yborder)
        x_offset = int(image.shape[1] * .8)
        image = cv2.putText(image, sat['desc'], (x_offset, image.shape[0] - yborder - y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)
        image = cv2.putText(image, channel['desc'], (x_offset, image.shape[0] - yborder),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size - 1,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)

    def centre_image():
        """centre the planet in the image"""
        def get_pixel_intensity(pi_x, pi_y):
            """get the pixel intensity"""
            # note range will be 0 - (255*3)
            return image[pi_y, pi_x][0] + image[pi_y, pi_x][1] + image[pi_y, pi_x][2]

        nonlocal image
        x_res = image.shape[1]
        y_res = image.shape[0]
        MY_LOGGER.debug('x_res = %d, y_res = %d', x_res, y_res)

        x_border = int(x_res * (456 / 5206))
        MY_LOGGER.debug('x_border = %d', x_border)

        # detect border via sampling
        MY_LOGGER.debug('Sampling test - left')
        left_int = 0
        for x in range(0, x_border, 20):
            for y in range(0, y_res - 1, 20):
                left_int += get_pixel_intensity(x, y)
        MY_LOGGER.debug('left_int = %d', left_int)

        MY_LOGGER.debug('Sampling test - right')
        right_int = 0
        for x in range(x_res - x_border - 1, x_res - 1, 20):
            for y in range(0, y_res - 1, 20):
                right_int += get_pixel_intensity(x, y)
        MY_LOGGER.debug('right_int = %d', right_int)

        if left_int > right_int:
            MY_LOGGER.debug('Left aligned')
            image = image[0:y_res-1, 0:x_res-x_border]
        else:
            MY_LOGGER.debug('Right aligned')
            image = image[0:y_res-1, x_border:x_res-1]


    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('sat_type = %s, sat = %s, type = %s, channel = %s, dir = %s, file = %s, extension = %s',
                     cb_sat_type, cb_sat, cb_type, cb_channel, cb_dir, cb_file, cb_extension)

    # load the image
    MY_LOGGER.debug('Reading file - %s', cb_dir + '/' + cb_file + cb_extension)
    image = cv2.imread(cb_dir + '/' + cb_file + cb_extension)

    # if GOES 13, then need to trim the image
    # as it is off centre to the left / right
    if cb_sat_type + cb_sat == 'goes13':
        MY_LOGGER.debug('GOES 13 - need to centre the image')
        centre_image()
    else:
        MY_LOGGER.debug('No need to centre image')


    font_size = int(image.shape[0] / 900)
    if font_size == 0:
        font_size = 1

    # find the config data for this combo
    for sat in BRANDING:
        if sat['sat'] == cb_sat_type + cb_sat:
            # MY_LOGGER.debug('sat = %s', cb_sat_type + cb_sat)
            for im_type in sat['types']:
                # MY_LOGGER.debug('type = %s', im_type)
                if im_type['type'] == cb_type:
                    MY_LOGGER.debug('type = %s', cb_type)
                    MY_LOGGER.debug('desc = %s', im_type['desc'])
                    for channel in im_type['channels']:
                        if channel['channel'] == cb_channel:
                            # MY_LOGGER.debug('channel = %s', cb_channel)
                            # MY_LOGGER.debug('desc = %s', channel['desc'])
                            y_offset = 26 * font_size
                            MY_LOGGER.debug('font size = %s, offset = %d', font_size, y_offset)
                            MY_LOGGER.debug('font colour = %d, %d, %d', channel['font colour'][0],
                                            channel['font colour'][1], channel['font colour'][2])

                            xborder = int(image.shape[1] / 55)
                            yborder = int(image.shape[0] / 55)
                            image_x = image.shape[1]
                            image_y = image.shape[0]
                            MY_LOGGER.debug('Image resolution - %d x %d', image_x, image_y)

                            MY_LOGGER.debug('Full disc image')
                            # add data into the image
                            MY_LOGGER.debug('Add data into the image')
                            add_kiwiweather()
                            if sat['acknowledge1']:
                                add_acknowledgement()
                            add_date(cb_date, cb_time)
                            add_sat_info()

                            # create directory (if needed)
                            MY_LOGGER.debug('Making directories for %s', WEB_PATH + cb_sat_type + cb_sat +\
                                             '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1] +\
                                                 '/' + cb_dir.split('/')[-3])
                            mk_dir(WEB_PATH + cb_sat_type + cb_sat)
                            mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type)
                            mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel)
                            mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])
                            mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1]  + '/' + cb_dir.split('/')[-3])

                            # cv2.imwrite(CODE_PATH + cb_sat_type + cb_sat + '_' + cb_type + '_' + cb_channel + cb_extension, image)

                            # write out image
                            output_file = WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1]  + '/' + cb_dir.split('/')[-3] + '/' + cb_file + '_web' + cb_extension
                            MY_LOGGER.debug('Saving to %s', output_file)
                            cv2.imwrite(output_file, image)
                            MY_LOGGER.debug('=' * 30)
                            return output_file


    MY_LOGGER.debug('Should not see this - validate branding.json')
    MY_LOGGER.error('Error with invalid branding.json data')


def proccess_satellite(sat_info):
    """process satellite info from web"""

    # set up variables
    file_directory = FILE_BASE + sat_info['File base']
    MY_LOGGER.debug('Satellite = %s', sat_info['Name'])
    MY_LOGGER.debug('file_directory = %s', file_directory)
    MY_LOGGER.debug('last directory = %s', sat_info['Last Directory'])
    MY_LOGGER.debug('URL = %s', sat_info['URL'])
    
    directories = sorted(listFD(sat_info['URL'], ''))

    # loop through directories
    for directory in directories:
        # MY_LOGGER.debug('directory = %s', directory)
        directory_datetime = directory.split('/')[5]

        # MY_LOGGER.debug('directory_datetime = %s', directory_datetime)

        if directory_datetime >= sat_info['Last Directory']:
            MY_LOGGER.debug('-' * 5)
            MY_LOGGER.debug('Need to process %s', directory_datetime)
            elements = directory_datetime.split('_')
            date_element = elements[0]
            MY_LOGGER.debug('date_element = %s', date_element)

            image_files = listFD(directory, 'png')
            channel_locator = len(sat_info['File in prefix']) + 1
            MY_LOGGER.debug('channel_locator = %s', channel_locator)

            # create directories
            MY_LOGGER.debug('file_directory = %s', file_directory)
            mk_dir(file_directory + '/' +  date_element)
            mk_dir(file_directory + '/' +  date_element + '/1')
            mk_dir(file_directory + '/' +  date_element + '/2')
            mk_dir(file_directory + '/' +  date_element + '/3')
            mk_dir(file_directory + '/' +  date_element + '/4')
            mk_dir(file_directory + '/' +  date_element + '/5')
            mk_dir(file_directory + '/' +  date_element + '/FC')

            # make directory for web files (goes13 only)
            if sat_info['Name'] == 'GOES 13':
                mk_dir(WEB_PATH + '/goes13/fd/1/' +  date_element)
                mk_dir(WEB_PATH + '/goes13/fd/2/' +  date_element)
                mk_dir(WEB_PATH + '/goes13/fd/3/' +  date_element)
                mk_dir(WEB_PATH + '/goes13/fd/4/' +  date_element)
                mk_dir(WEB_PATH + '/goes13/fd/5/' +  date_element)
                mk_dir(WEB_PATH + '/goes13/fd/FC/' +  date_element)

            existsCount = 0

            for file in image_files:
                filename = file.split('/')[-1]
                if sat_info['File in prefix'] in filename:
                    MY_LOGGER.debug('filename = %s', filename)
                    channel = '?'
                    if filename[channel_locator] == 'F':
                        file_location = file_directory + '/' + date_element + '/FC/'
                        channel = 'FC'
                    else:
                        file_location = file_directory + '/' + date_element + '/' + filename[channel_locator] + '/'
                        channel = filename[channel_locator]

                    MY_LOGGER.debug('file_location = %s', file_location)
                    MY_LOGGER.debug('channel = %s', channel)

                    # see if file exists, if not, get it
                    if not os.path.exists(file_location + filename.replace('.png', '.jpg')):
                        # get file
                        MY_LOGGER.debug('Getting file %s', filename)

                        data = requests.get(file)
                        MY_LOGGER.debug('Writing file %s', filename)
                        open(file_location + filename, 'wb').write(data.content)
                        # non-channel 1 and FC images are ~5k x 5k pixels
                        # channel 1 and FC images are 20832 x 18956 ~190MB each
                        # convert all to jpg images, aligned with GOES images size, which are 5424x5424
                        # keeping  the correct aspect ratio so 5424 x 4936
                        if channel not in ('1', 'FC'):
                            ratio = ' 1'
                        else:
                            ratio = ' 0.2604'

                        cmd = 'vips resize ' + file_location + filename + ' ' + file_location + filename.replace('.png', '.jpg') + ratio
                        MY_LOGGER.debug('cmd %s', cmd)
                        wxcutils.run_cmd(cmd)

                        # can now delete the original image to save space
                        wxcutils.run_cmd('rm ' + file_location + filename)

                        if sat_info['Name'] == 'GOES 13':
                            bits = filename.split('_')
                            for bit in bits:
                                MY_LOGGER.debug('bit %s', bit)
                            year = bits[-1][:4]
                            month = calendar.month_abbr[int(bits[-1][4:6])]
                            day = bits[-1][6:8]
                            hour = bits[-1][9:11]
                            min = bits[-1][11:13]
                            MY_LOGGER.debug('year = %s, month = %s, day = %s, hour = %s min = %s', year, month, day, hour, min)
                            im_date = day + '-' + month + '-' + year
                            im_time = hour + ':' + min + ' UTC'

                            MY_LOGGER.debug('Creating branded image - %s, date %s, time %s', channel, im_date, im_time)

                            web_file = create_branded('goes', '13', 'fd', channel, file_location, filename.replace('.png', ''), '.jpg', im_date, im_time)

                            # copy to output directory
                            new_filename = 'goes13-' + channel + '.jpg'
                            MY_LOGGER.debug('new_filename = %s', new_filename)
                            wxcutils.copy_file(web_file,
                                               os.path.join(OUTPUT_PATH,
                                                            new_filename))
                        else:
                            # non-GOES 13
                            # copy file to output folder
                            wxcutils.copy_file(file_location + filename.replace('.png', '.jpg'), OUTPUT_PATH + sat_info['File out prefix'] + '-' + channel + '.jpg')

                        # create thumbnail and txt file
                        cmd = 'vips resize ' + OUTPUT_PATH + sat_info['File out prefix'] + '-' + channel + '.jpg' + ' ' + OUTPUT_PATH + sat_info['File out prefix'] + '-' + channel + '-tn.jpg' + ' 0.1'
                        MY_LOGGER.debug('cmd %s', cmd)
                        wxcutils.run_cmd(cmd)

                        # create file with date time info
                        MY_LOGGER.debug('Writing out last generated date file')
                        wxcutils.save_file(OUTPUT_PATH, sat_info['File out prefix'] + '-' + channel + '.txt', get_last_generated_text(filename.replace('.png', '.jpg')))

                    else:
                        MY_LOGGER.debug('Already exists %s', file_location + filename)
                        existsCount += 1

                # check age of directory to skip over "OLD" directories
                # 2021-08-11_16-56
                directory_datetime_dt = datetime.datetime.strptime(directory_datetime, '%Y-%m-%d_%H-%M')
                directory_datetime_epoch = wxcutils.utc_datetime_to_epoch(directory_datetime_dt)
                current_epoch = time.time()
                directory_age= current_epoch - float(directory_datetime_epoch)
                MY_LOGGER.debug('current_epoch = %f', current_epoch)
                MY_LOGGER.debug('directory_datetime_epoch = %f', float(directory_datetime_epoch))
                MY_LOGGER.debug('age = %f', directory_age)


                if existsCount == 6 or directory_age > (6 * 60 * 60):
                    if existsCount == 6:
                        MY_LOGGER.debug('all 6 files exist - update last directory')
                    else:
                        MY_LOGGER.debug('Directory age is too old, assuming files will not appear - 6 hours')
                    if directory_datetime > sat_info['Last Directory']:
                        MY_LOGGER.debug('Old last directory = %s, new last directory = %s', sat_info['Last Directory'], directory_datetime)
                        sat_info['Last Directory'] = directory_datetime
                    else:
                        MY_LOGGER.debug('No change required - Old last directory = %s, new last directory = %s', sat_info['Last Directory'], directory_datetime)




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
MODULE = 'web'
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

# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]
MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

FILE_BASE = '/home/pi/goes/'
MY_LOGGER.debug('FILE_BASE = %s', FILE_BASE)

WEB_PATH = FILE_BASE + 'web/'

# load logo and branding info
LOGOBLACK = cv2.imread(CONFIG_PATH + 'logo-black.jpg')
LOGOWHITE = cv2.imread(CONFIG_PATH + 'logo-white.jpg')
BRANDING = wxcutils.load_json(CONFIG_PATH, 'branding.json')

# get the last directory name used for a sync
SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'web.json')

# loop through active satellites
for key, value in SATELLITE_INFO.items():
        for si in SATELLITE_INFO[key]:
            if si['Active'] == 'yes':
                MY_LOGGER.debug('-' * 20)
                MY_LOGGER.debug(si)
                try:
                    proccess_satellite(si)
                except:
                    MY_LOGGER.debug('Exception whilst processing satellite %s', si['Name'])
                    MY_LOGGER.error('Loop exception handler: %s %s %s',
                                    sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

# save updated config
wxcutils.save_json(CONFIG_PATH, 'web.json', SATELLITE_INFO)


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
