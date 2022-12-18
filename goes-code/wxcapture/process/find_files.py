#!/usr/bin/env python3
"""find files to migrate"""


# import libraries
import os
import time
import glob
import math
import subprocess
import calendar
from datetime import datetime
import cv2
import wxcutils


def kill_old_process(pa_text, pa_age):
    """kill old processes over an threshold age"""

    MY_LOGGER.debug('pa_text = %s', pa_text)
    pa_pid = pa_text.split()[1]
    MY_LOGGER.debug('pa_pid = %s', pa_pid)

    pa_time = 0
    try:
        cmd = subprocess.Popen(('ps', '-p', pa_pid, '-o', 'etimes'),
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = cmd.communicate()
        MY_LOGGER.debug('output = %s', stdout.decode('utf-8'))
        pa_time = stdout.decode('utf-8').splitlines()[1]
        MY_LOGGER.debug('pa_time = %s', pa_time)
    except:
        # note this unlikely unless process has completed very recently
        MY_LOGGER.debug('%s is NOT running???', pa_text)

    if int(pa_time) > int(pa_age):
        # kill process
        MY_LOGGER.debug('Killing process as running too long - %s', pa_text)
        wxcutils.run_cmd('kill ' + str(pa_pid))
        return True

    MY_LOGGER.debug('Process is young enough - %s', pa_text)
    return False


def number_processes(process_name):
    """see how many processes are running"""
    try:
        cmd = subprocess.Popen(('ps', '-ef'), stdout=subprocess.PIPE)
        output = subprocess.check_output(('grep', process_name), stdin=cmd.stdout)
        cmd.wait()
        MY_LOGGER.debug('output = %s', output.decode('utf-8'))
        process_count = 0
        lines = output.decode('utf-8').splitlines()
        for line in lines:
            if 'grep' in line or '/bin/bash' in line:
                # ignore grep or cron lines
                process_count += 0
            else:
                # get age and kill if too old (20 minutes)
                if kill_old_process(line, 1200):
                    process_count += 0
                else:
                    process_count += 1
        MY_LOGGER.debug('%d process(es) are running', process_count)
        return process_count
    except:
        # note this should not be possible!
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return 0


def mk_dir(directory):
    """only create if it does not already exist"""
    MY_LOGGER.debug('Make? %s', directory)
    if not os.path.isdir(directory):
        wxcutils.make_directory(directory)


def find_directories(directory):
    """find directories in directory"""
    directory_set = []
    for directories in os.listdir(directory):
        directory_set.append(directories)
    return directory_set


def find_latest_directory(directory):
    """find latest directory in directory"""
    latest = 0
    latest_dir = ''
    for directories in os.listdir(directory):
        MY_LOGGER.debug('directories %s', directories)
        directories_num = int(directories.replace('-', ''))
        if directories_num > latest:
            latest = directories_num
            latest_dir = directories
    return str(latest_dir)


def find_latest_file(directory):
    """find latest file in directory based on last modified timestamp"""
    latest_timestamp = 0.0
    latest_filename = ''
    for filename in os.listdir(directory):
        file_timestamp = os.path.getmtime(os.path.join(directory, filename))
        if file_timestamp > latest_timestamp:
            latest_filename = filename
            latest_timestamp = file_timestamp
    MY_LOGGER.debug('latest_filename = %s, latest_timestamp = %f',
                    latest_filename, latest_timestamp)
    return latest_filename


def find_latest_file_contains(directory, contains):
    """find latest file matching a pattern in directory based on last modified timestamp"""
    latest_timestamp = 0.0
    latest_filename = ''
    for filename in os.listdir(directory):
        if contains in filename:
            file_timestamp = os.path.getmtime(os.path.join(directory, filename))
            if file_timestamp > latest_timestamp:
                latest_filename = filename
                latest_timestamp = file_timestamp
    MY_LOGGER.debug('latest_filename = %s, latest_timestamp = %f', latest_filename,
                    latest_timestamp)
    return latest_filename


def find_latest_filename_contains(directory, contains):
    """find latest file matching a pattern in directory based on the filename"""
    # example filename
    # 20201107090002-pacsfc24_latestBW.gif
    latest_dt = 0
    latest_filename = ''
    for filename in os.listdir(directory):
        if contains in filename:
            file_dt = (int)(filename.split('-')[0])
            if file_dt > latest_dt:
                latest_dt = file_dt
                latest_filename = filename
    MY_LOGGER.debug('latest_filename = %s, latest_dt = %f', latest_filename, latest_dt)
    return latest_filename


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


def create_thumbnail(ct_directory, ct_extension):
    """create thumbnail of the image"""
    wxcutils.run_cmd('convert \"' + OUTPUT_PATH + ct_directory + ct_extension +
                     '\" -resize 9999x500 ' + OUTPUT_PATH + ct_directory + '-tn' + ct_extension)


def do_sanchez(ds_src, ds_dest, ds_channel):
    """do sanchez processing on the image file"""
    MY_LOGGER.debug('Sanchez processing %s %s', ds_src, ds_dest)
    if ds_channel == 'fc':
        MY_LOGGER.debug('Doing full colour sanchez')
        cmd = '/home/pi/sanchez/Sanchez reproject -s ' + ds_src + ' -o ' + ds_dest + ' -ULa -r 4 -f -D ' + CONFIG_PATH + \
              'Satellites-FC.json'
    else:
        MY_LOGGER.debug('Doing IR sanchez')
        cmd = '/home/pi/sanchez/Sanchez reproject -u ' + CONFIG_PATH + 'world.2004' + str(datetime.now().month).zfill(2) + \
              '.3x5400x2700.jpg -s ' + ds_src + ' -o ' + ds_dest + ' -La -r 4 -f  -D ' + CONFIG_PATH + \
              'Satellites-IR.json'
    MY_LOGGER.debug(cmd)
    wxcutils.run_cmd(cmd)
    MY_LOGGER.debug('Sanchez processing completed')


def do_combined_sanchez(ds_dest, ds_date_time):
    """do combined sanchez processing"""
    MY_LOGGER.debug('Combined sanchez processing %s %s', ds_dest, ds_date_time)
    cmd = '/home/pi/sanchez/Sanchez reproject -u ' + CONFIG_PATH + 'world.2004' + str(datetime.now().month).zfill(2) + \
          '.3x5400x2700.jpg -s ' + BASEDIR + ' -o ' + ds_dest + ' -T ' + ds_date_time + ' -a -f -d 90 -D ' + CONFIG_PATH + \
          'Satellites-IR.json'
    MY_LOGGER.debug(cmd)
    wxcutils.run_cmd(cmd)
    MY_LOGGER.debug('Combined sanchez processing completed')


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
        x_offset = int(image.shape[1] * .77)
        image = cv2.putText(image, sat['acknowledge1'], (x_offset, yborder + (y_offset * 1)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)
        image = cv2.putText(image, sat['acknowledge2'], (x_offset, yborder + (y_offset * 2)),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)


    def add_date(ad_date, ad_time):
        """add date and time"""
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
        nonlocal image
        MY_LOGGER.debug('%d, %d, %d', image.shape[1], (80 * len(channel['desc'])), yborder)
        x_offset = int(image.shape[1] * .77)
        image = cv2.putText(image, sat['desc'], (x_offset, image.shape[0] - yborder - y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)
        image = cv2.putText(image, channel['desc'], (x_offset, image.shape[0] - yborder),
                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                            font_size, cv2.LINE_AA)


    MY_LOGGER.debug('=' * 30)
    MY_LOGGER.debug('sat_type = %s, sat = %s, type = %s, channel = %s, dir = %s, file = %s, extension = %s', cb_sat_type, cb_sat, cb_type, cb_channel, cb_dir, cb_file, cb_extension)

    # load the image
    MY_LOGGER.debug('Reading file - %s', cb_dir + '/' + cb_file + cb_extension)
    image = cv2.imread(cb_dir + '/' + cb_file + cb_extension)
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
                            MY_LOGGER.debug('font colour = %d, %d, %d', channel['font colour'][0], channel['font colour'][1], channel['font colour'][2])

                            xborder = int(image.shape[1] / 55)
                            yborder = int(image.shape[0] / 55)
                            image_x = image.shape[1]
                            image_y = image.shape[0]
                            MY_LOGGER.debug('Image resolution - %d x %d', image_x, image_y)

                            if cb_sat_type == 'combined':
                                MY_LOGGER.debug('Combined image')

                                # add data to header / footer
                                MY_LOGGER.debug('add data to header / footer')
                                scaler = image_y / 1500
                                branding_height = int(LOGOBLACK.shape[0] * scaler)
                                if branding_height < 125:
                                    branding_height = 125

                                # add the border to the top of the image
                                image = cv2.copyMakeBorder(image, branding_height, 0, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
                                image_y += branding_height
                                MY_LOGGER.debug('New image resolution - %d x %d', image_x, image_y)

                                # add in the logo
                                new_x = int(LOGOBLACK.shape[1] * scaler)
                                new_y = int(LOGOBLACK.shape[0] * scaler)
                                scaled_logo = cv2.resize(LOGOBLACK, (new_x, new_y), interpolation=cv2.INTER_AREA)
                                image[0:scaled_logo.shape[0], image_x-scaled_logo.shape[1]:image_x+scaled_logo.shape[1]] = scaled_logo

                                # Kiwiweather.com
                                image = cv2.putText(image, 'KiwiWeather.com ZL4MDE', (xborder, yborder + y_offset),
                                                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                            2, cv2.LINE_AA)
                                # Acknowledgement
                                image = cv2.putText(image, sat['acknowledge1'].split(':')[0] + ' ' + sat['acknowledge2'], (xborder, yborder + (y_offset * 2)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                    (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                    font_size, cv2.LINE_AA)

                                # add date
                                image = cv2.putText(image, cb_date + ' ' + cb_time, (xborder, yborder + (y_offset * 3)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                    (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                    font_size, cv2.LINE_AA)

                                # add sat info
                                image = cv2.putText(image, sat['desc'] + ' ' + im_type['desc'] + ' ' + channel['desc'], (xborder, yborder + (y_offset * 4)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                    (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                    font_size, cv2.LINE_AA)

                                # MY_LOGGER.debug('Saving to %s', CODE_PATH + cb_sat_type + cb_sat + '_' + cb_type + '_' + cb_channel + cb_extension)
                                # cv2.imwrite(CODE_PATH + cb_sat_type + cb_sat + '_' + cb_type + '_' + cb_channel + cb_extension, image)

                                # raise Exception('check image created')

                                # create directory (if needed)
                                MY_LOGGER.debug('Making directories for %s', WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])

                                # write out image
                                output_file = WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1] + '/' + cb_file + '_web' + cb_extension
                                MY_LOGGER.debug('Saving to %s', output_file)
                                cv2.imwrite(output_file, image)


                                MY_LOGGER.debug('=' * 30)
                                return output_file
                            elif cb_type in ('m1', 'm2') or cb_channel in ('fcsanchez', 'ch13sanchez', 'IRsanchez'):
                                MY_LOGGER.debug('M1 / M2 image or sanchez reprojection')
                                
                                # add data to header / footer
                                MY_LOGGER.debug('add data to header / footer')
                                scaler = image_y / 1400
                                branding_height = int(LOGOBLACK.shape[0] * scaler)
                                if branding_height < 125:
                                    branding_height = 125

                                # add the border to the top of the image
                                image = cv2.copyMakeBorder(image, branding_height, 0, 0, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))
                                image_y += branding_height
                                MY_LOGGER.debug('New image resolution - %d x %d', image_x, image_y)

                                # add in the logo
                                new_x = int(LOGOBLACK.shape[1] * scaler)
                                new_y = int(LOGOBLACK.shape[0] * scaler)
                                scaled_logo = cv2.resize(LOGOBLACK, (new_x, new_y), interpolation=cv2.INTER_AREA)
                                image[0:scaled_logo.shape[0], image_x-scaled_logo.shape[1]:image_x+scaled_logo.shape[1]] = scaled_logo

                                # Kiwiweather.com
                                image = cv2.putText(image, 'KiwiWeather.com ZL4MDE', (xborder, yborder + y_offset),
                                                            cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                            (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                            2, cv2.LINE_AA)
                                # Acknowledgement
                                image = cv2.putText(image, sat['acknowledge1'].split(':')[0] + ' ' + sat['acknowledge2'], (xborder, yborder + (y_offset * 2)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                    (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                    font_size, cv2.LINE_AA)

                                # add date
                                image = cv2.putText(image, cb_date + ' ' + cb_time, (xborder, yborder + (y_offset * 3)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                    (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                    font_size, cv2.LINE_AA)

                                # add sat info
                                image = cv2.putText(image, sat['desc'] + ' ' + im_type['desc'] + ' ' + channel['desc'], (xborder, yborder + (y_offset * 4)),
                                                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                                                    (channel['font colour'][0], channel['font colour'][1], channel['font colour'][2]),
                                                    font_size, cv2.LINE_AA)

                                # cv2.imwrite(CODE_PATH + cb_sat_type + cb_sat + '_' + cb_type + '_' + cb_channel + cb_extension, image)

                                # raise Exception('check image created')

                                # write out image as is without modifications
                                # create directory (if needed)
                                MY_LOGGER.debug('Making directories for %s', WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])

                                # write out image
                                output_file = WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1] + '/' + cb_file + '_web' + cb_extension
                                MY_LOGGER.debug('Saving to %s', output_file)
                                cv2.imwrite(output_file, image)
                                MY_LOGGER.debug('=' * 30)
                                return output_file
                            elif cb_type == 'fd':
                                MY_LOGGER.debug('Full disc image')
                                # add data into the image
                                MY_LOGGER.debug('Add data into the non-m1/m2 image')
                                add_kiwiweather()
                                if sat['acknowledge1']:
                                    add_acknowledgement()
                                add_date(cb_date, cb_time)
                                add_sat_info()

                                # create directory (if needed)
                                MY_LOGGER.debug('Making directories for %s', WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel)
                                mk_dir(WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1])

                                # cv2.imwrite(CODE_PATH + cb_sat_type + cb_sat + '_' + cb_type + '_' + cb_channel + cb_extension, image)

                                # write out image
                                output_file = WEB_PATH + cb_sat_type + cb_sat + '/' + cb_type + '/' + cb_channel + '/' + cb_dir.split('/')[-1] + '/' + cb_file + '_web' + cb_extension
                                MY_LOGGER.debug('Saving to %s', output_file)
                                cv2.imwrite(output_file, image)
                                MY_LOGGER.debug('=' * 30)
                                return output_file


    MY_LOGGER.debug('Should not see this - validate branding.json')
    MY_LOGGER.error('Error with invalid branding.json data')


def process_goes(sat_num):
    """process GOES xx files using standard directory structure"""

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'goes' + sat_num
    MY_LOGGER.debug('GOES%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    # find directories
    type_directories = find_directories(sat_dir)
    for type_directory in type_directories:
        MY_LOGGER.debug('--')
        MY_LOGGER.debug('type_directory = %s', type_directory)
        channels_directory = os.path.join(sat_dir, type_directory)
        MY_LOGGER.debug('channels_directory = %s', channels_directory)
        channels_directories = find_directories(channels_directory)
        for channel_directory in channels_directories:
            MY_LOGGER.debug('---')
            MY_LOGGER.debug('channel_directory = %s', channel_directory)
            search_directory = os.path.join(channels_directory, channel_directory)
            MY_LOGGER.debug('search_directory = %s', search_directory)
            latest_directory = find_latest_directory(search_directory)
            MY_LOGGER.debug('latest_directory = %s', latest_directory)

            # find the latest file
            latest_dir = os.path.join(search_directory, latest_directory)
            latest_file = find_latest_file(latest_dir)
            MY_LOGGER.debug('latest_file = %s', latest_file)
            filename, extenstion = os.path.splitext(latest_file)
            new_filename = 'goes_' + sat_num + '_' + type_directory + '_' + channel_directory

            # see when last saved
            stored_timestamp = 0.0
            try:
                stored_timestamp = LATESTTIMESTAMPS[new_filename + extenstion]
            except NameError:
                pass
            except KeyError:
                pass

            # date time for original file
            latest = os.path.getmtime(os.path.join(latest_dir, latest_file))

            MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

            if stored_timestamp != int(latest):
                # new file found which hasn't yet been copied over

                # date / time info
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

                web_file = create_branded('goes', sat_num, type_directory, channel_directory, latest_dir, filename, extenstion, im_date, im_time)

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(web_file,
                                   os.path.join(OUTPUT_PATH,
                                                new_filename + extenstion))

                # create thumbnail
                create_thumbnail(new_filename, extenstion)

                 # create file with date time info
                wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', get_last_generated_text(new_filename))

                # update latest
                LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)

                # generate sanchez FC image if GOES 17 / 18  and fd and fc/ch13 image
                if sat_num in ('17', '18') and type_directory == 'fd' and channel_directory in ['fc', 'ch13']:
                    sanchez_dir = SANCHEZ_PATH + 'goes' + sat_num + '/' + type_directory + '/' + channel_directory + '/'
                    # create directory (if needed)
                    mk_dir(sanchez_dir)
                    mk_dir(sanchez_dir + latest_directory)
                    san_file_dir = sanchez_dir + latest_directory

                    # create sanchez image
                    do_sanchez(os.path.join(latest_dir, latest_file),
                               san_file_dir + '/' + latest_file.replace('.jpg', '-sanchez.jpg'),
                               channel_directory)

                    web_file = create_branded('goes', sat_num, 'fd', channel_directory + 'sanchez', san_file_dir, latest_file.replace('.jpg', '-sanchez'), '.jpg', im_date, im_time)

                    # copy to output directory
                    MY_LOGGER.debug('new_filename = %s', new_filename)
                    wxcutils.copy_file(web_file,
                                       os.path.join(OUTPUT_PATH, new_filename + '-sanchez' + extenstion))

                    # create thumbnail
                    create_thumbnail(new_filename + '-sanchez', extenstion)

                    # create file with date time info
                    wxcutils.save_file(OUTPUT_PATH, new_filename + '-sanchez' + '.txt', get_last_generated_text(new_filename))

                    # if file is a GOES17 (or 18) / fd / ch13, then do a stitch of all available sats
                    # GOES 16 / 17 / 18 / Himawari 9 / GK-2A
                    # at the current UTC time
                    if sat_num in ('17', '18') and type_directory == 'fd' and channel_directory == 'ch13':
                        # create directory (if needed)
                        combined_dir = SANCHEZ_PATH + 'combined' + '/'
                        combined_file_dir = combined_dir + 'fd/ir/' + latest_directory

                        MY_LOGGER.debug('Latest file epoch = %f', latest)
                        # example 1612641000 => 2021-02-06T19:50:00
                        combined_date_time = wxcutils.epoch_to_utc(latest, '%Y-%m-%dT%H:%M:%S')
                        op_filename = combined_date_time.replace(':', '-').replace('T', '-')
                        MY_LOGGER.debug('op_filename = %s', op_filename)

                        # create combined sanchez image
                        do_combined_sanchez(combined_file_dir  + '/' + op_filename + '.jpg', combined_date_time)

                        web_file = create_branded('combined', '', 'fd', 'ir', combined_file_dir, op_filename, '.jpg', im_date, im_time)

                        # copy to output directory
                        MY_LOGGER.debug('new_filename = %s', new_filename)
                        MY_LOGGER.debug('>>%s<< %d', web_file, len(web_file))
                        wxcutils.copy_file(web_file,
                                           os.path.join(OUTPUT_PATH,
                                                        'combined.jpg'))

                        # create thumbnail
                        create_thumbnail('combined', '.jpg')

                        # create file with date time info
                        wxcutils.save_file(OUTPUT_PATH, 'combined.txt', get_last_generated_text('combined.txt'))

                    # update latest
                    LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)



    MY_LOGGER.debug('---------------------------------------------')


def process_goes_2(sat_num):
    """process GOES xx files using non-standard directory structure
       based on Himawari code"""

    # Note that this code only looks in the latest directory only
    # It is possible that there is a later image of a type only in
    # a previous day's file, but this will be missed with the
    # current search approach

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'goes' + sat_num
    MY_LOGGER.debug('GOES%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    image_types = ['IR', 'WV']

    # find directories
    type_directories = find_directories(sat_dir)
    for type_directory in type_directories:
        MY_LOGGER.debug('--')
        MY_LOGGER.debug('type_directory = %s', type_directory)
        channels_directory = os.path.join(sat_dir, type_directory)

        latest_directory = find_latest_directory(channels_directory)
        MY_LOGGER.debug('latest_directory = %s', latest_directory)
        latest_dir = os.path.join(os.path.join(sat_dir, type_directory), latest_directory)
        MY_LOGGER.debug('latest_dir = %s', latest_dir)

        for image_type in image_types:
            MY_LOGGER.debug('image_type = %s', image_type)
            latest_file = find_latest_file_contains(latest_dir, image_type)
            MY_LOGGER.debug('latest_file = %s', latest_file)

            # only process if there is a file to process
            if latest_file:

                filename, extenstion = os.path.splitext(latest_file)
                new_filename = 'goes_' + sat_num + '_' + type_directory + '_' + image_type

                # see when last saved
                stored_timestamp = 0.0
                try:
                    stored_timestamp = LATESTTIMESTAMPS[new_filename + extenstion]
                except NameError:
                    pass
                except KeyError:
                    pass

                # date time for original file
                latest = os.path.getmtime(os.path.join(latest_dir, latest_file))

                MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

                if stored_timestamp != int(latest):
                    # new file found which hasn't yet been copied over


                    # need to implement when GOES 15 is active
                    # base on goes code, below is a fragment...
                    #     # date / time info
                    #     bits = filename.split('_')
                    #     for bit in bits:
                    #         MY_LOGGER.debug('bit %s', bit)
                    #     year = bits[-1][:4]
                    #     month = calendar.month_abbr[int(bits[-1][4:6])]
                    #     day = bits[-1][6:8]
                    #     hour = bits[-1][9:11]
                    #     min = bits[-1][11:13]
                    #     MY_LOGGER.debug('year = %s, month = %s, day = %s, hour = %s min = %s', year, month, day, hour, min)
                    #     im_date = day + '-' + month + '-' + year
                    #     im_time = hour + ':' + min + ' UTC'

                    #     create_branded('goes', sat_num, type_directory, channel_directory, latest_dir, filename, extenstion, im_date, im_time)



                    # copy to output directory
                    MY_LOGGER.debug('new_filename = %s', new_filename)
                    wxcutils.copy_file(os.path.join(latest_dir, latest_file),
                                       os.path.join(OUTPUT_PATH,
                                                    new_filename + extenstion))

                    # create thumbnail
                    create_thumbnail(new_filename, extenstion)

                    # create file with date time info
                    wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', get_last_generated_text(new_filename))

                    # update latest
                    LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)
            else:
                MY_LOGGER.debug('no file to process')

    MY_LOGGER.debug('---------------------------------------------')


def process_himawari(sat_num):
    """process Himawari xx files"""

    # Note that this code only looks in the latest directory only
    # It is possible that there is a later image of a type only in
    # a previous day's file, but this will be missed with the
    # current search approach

    MY_LOGGER.debug('---------------------------------------------')
    sat_dir = BASEDIR + 'himawari' + sat_num
    MY_LOGGER.debug('Himawari%s', sat_num)
    MY_LOGGER.debug('sat_dir = %s', sat_dir)

    image_types = ['IR', 'VS', 'WV']

    # find directories
    type_directories = find_directories(sat_dir)
    for type_directory in type_directories:
        MY_LOGGER.debug('--')
        MY_LOGGER.debug('type_directory = %s', type_directory)
        channels_directory = os.path.join(sat_dir, type_directory)

        latest_directory = find_latest_directory(channels_directory)
        MY_LOGGER.debug('latest_directory = %s', latest_directory)
        latest_dir = os.path.join(os.path.join(sat_dir, type_directory), latest_directory)
        MY_LOGGER.debug('latest_dir = %s', latest_dir)

        for image_type in image_types:
            MY_LOGGER.debug('image_type = %s', image_type)
            latest_file = find_latest_file_contains(latest_dir, image_type)
            MY_LOGGER.debug('latest_file = %s', latest_file)

            filename, extenstion = os.path.splitext(latest_file)
            new_filename = 'himawari_' + sat_num + '_' + type_directory + '_' + image_type

            # see when last saved
            stored_timestamp = 0.0
            try:
                stored_timestamp = LATESTTIMESTAMPS[new_filename + extenstion]
            except NameError:
                pass
            except KeyError:
                pass

            # date time for original file
            latest = os.path.getmtime(os.path.join(latest_dir, latest_file))

            MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

            # date / time info
            bits = filename.split('_')
            # for bit in bits:
            #     MY_LOGGER.debug('bit %s', bit)
            year = bits[-1][:4]
            month = calendar.month_abbr[int(bits[-1][4:6])]
            day = bits[-1][6:8]
            hour = bits[-1][9:11]
            min = bits[-1][11:13]
            MY_LOGGER.debug('year = %s, month = %s, day = %s, hour = %s min = %s', year, month, day, hour, min)
            im_date = day + '-' + month + '-' + year
            im_time = hour + ':' + min + ' UTC'

            web_file = create_branded('himawari', '9', type_directory, bits[2], latest_dir, filename, extenstion, im_date, im_time)

            # copy to output directory
            MY_LOGGER.debug('new_filename = %s', new_filename)
            wxcutils.copy_file(web_file,
                                os.path.join(OUTPUT_PATH,
                                            new_filename + extenstion))

            # create thumbnail
            create_thumbnail(new_filename, extenstion)

                # create file with date time info
            wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', get_last_generated_text(new_filename))

            # update latest
            LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)

            # for IR full disc images, create a projected image
            if image_type == 'IR' and type_directory  == 'fd':
                sanchez_dir = SANCHEZ_PATH + 'himawari9/' + type_directory + '/' + image_type + '/'
                MY_LOGGER.debug('sanchez_dir = %s', sanchez_dir)

                # create directory (if needed)
                mk_dir(sanchez_dir)
                mk_dir(sanchez_dir + latest_directory)
                san_file_dir = sanchez_dir + latest_directory

                # create sanchez image
                do_sanchez(os.path.join(latest_dir, latest_file),
                            san_file_dir + '/' + latest_file.replace(extenstion, '-sanchez' + extenstion),
                            image_type)
                
                web_file = create_branded('himawari', sat_num, type_directory, image_type + 'sanchez', san_file_dir, latest_file.replace(extenstion, '-sanchez'), extenstion, im_date, im_time)

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(web_file,
                                   os.path.join(OUTPUT_PATH, new_filename + '-sanchez' + extenstion))

                # create thumbnail
                create_thumbnail(new_filename + '-sanchez', extenstion)

                # create file with date time info
                wxcutils.save_file(OUTPUT_PATH, new_filename + '-sanchez' + '.txt', get_last_generated_text(new_filename))

                # update latest
                LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)

    MY_LOGGER.debug('---------------------------------------------')


def process_nws():
    """process nws files"""

    MY_LOGGER.debug('---------------------------------------------')
    MY_LOGGER.debug('NWS')
    nws_dir = BASEDIR + 'nws/'
    MY_LOGGER.debug('nws_dir = %s', nws_dir)

    # get list of directories
    directories = find_directories(nws_dir)

    # loop through directories to find files
    for directory in directories:
        MY_LOGGER.debug('directory = %s', directory)
        for filename in os.listdir(nws_dir + directory):
                MY_LOGGER.debug('filename = %s', filename)

                base_filename, extenstion = os.path.splitext(filename)
                # remove the first 17 characters to remove the date time part
                new_filename = 'nws_' + base_filename[17:]

                # see when last saved
                stored_timestamp = 0.0
                try:
                    stored_timestamp = LATESTTIMESTAMPS[new_filename + extenstion]
                except NameError:
                    pass
                except KeyError:
                    pass

                # date time for original file
                latest = os.stat(nws_dir + directory + '/' + filename).st_mtime

                MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

                # if latest is newer than the stored one
                if stored_timestamp < int(latest):
                    # new file found which hasn't yet been copied over
                    # copy to output directory
                    MY_LOGGER.debug('new_filename = %s', new_filename)
                    wxcutils.copy_file(nws_dir + directory + '/' + filename,
                                       os.path.join(OUTPUT_PATH, new_filename + extenstion))

                    # create thumbnail
                    create_thumbnail(new_filename, extenstion)

                    # create file with date time info
                    wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', get_last_generated_text(new_filename))

                    # update latest
                    LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)


    MY_LOGGER.debug('---------------------------------------------')


def create_animation(ca_satellite, ca_directory, ca_file_match, ca_frames, ca_duration, ca_resolution, ca_selection, ca_min_size, ca_end_frame):
    """create animation from images - type / channel / date format directories"""

    MY_LOGGER.debug('create_animation satellite = %s, directory = %s, file_match = %s, frames = %s, duration = %s, resolution = %s, selection = %s, min_size = %s, end_frame = %s',
                    ca_satellite, ca_directory, ca_file_match, ca_frames, ca_duration, ca_resolution, ca_selection, ca_min_size, ca_end_frame)

    # filename
    ca_filename = ca_directory.replace('/', '-') + '-' + str(ca_frames) + '-' + ca_resolution.replace(':', 'x')
    MY_LOGGER.debug('ca_filename = %s', ca_filename)

    # generate animation file

    # get list of all directories, sorted by date
    # reverse order so can get the last ca_frames
    ca_directories = find_directories(BASEDIR + ca_directory)
    ca_directories.sort(reverse=True)
    # MY_LOGGER.debug('ca_directories = %s', ca_directories)

    # loop through directories until we get required
    # number of frames or run out of directories
    ca_text = ''
    ca_frame_counter = 0
    ca_end_frame = 'file \'' + CONFIG_PATH + 'end-frame.jpg' + '\'' + os.linesep
    ca_duration_text = 'duration ' + str(ca_duration) + os.linesep
    for ca_dir in ca_directories:
        # loop through files in each directory
        MY_LOGGER.debug('looking in %s', BASEDIR + ca_directory + '/' + ca_dir + '/' + ca_file_match)
        ca_frame_list = glob.glob(BASEDIR + ca_directory + '/' + ca_dir + '/' + ca_file_match)
        ca_frame_list.sort(reverse=True)
        # MY_LOGGER.debug('ca_frame_list = %s', ca_frame_list)
        for ca_line in ca_frame_list:
            # MY_LOGGER.debug('ca_line = %s', ca_line)
            if ca_selection == 'ALL' or (ca_selection == 'LIGHT' and os.path.getsize(ca_line) >= ca_min_size):
                ca_entry = 'file \'' + ca_line + '\'' + os.linesep
                if ca_satellite == 'GOES13' and (ca_line[57:63] == 'T00455' or ca_line[57:63] == 'T15455'):
                    MY_LOGGER.debug('Skipping GOES 13 offcentre frame')
                else:
                    if ca_frame_counter == 0:
                        # this is the last frame to render, to also add end frame
                        if ca_end_frame == 'Y':
                            ca_text = ca_entry + ca_duration_text + ca_end_frame
                    else:
                        ca_text = ca_entry + ca_duration_text + ca_text
                    ca_frame_counter += 1
                if ca_frame_counter >= ca_frames:
                    MY_LOGGER.debug('got enough frames - inner loop')
                    break
        if ca_frame_counter >= ca_frames:
            MY_LOGGER.debug('got enough frames - outer loop')
            break

    # save text to file
    wxcutils.save_file(WORKING_PATH, ca_filename + '.txt', ca_text)

    # animate the frame list
    wxcutils.run_cmd('ffmpeg -y -safe 0 -f concat -i ' + WORKING_PATH + ca_filename + '.txt' +
                     ' -c:v libx264 -pix_fmt yuv420p -vf scale=' + ca_resolution + ' ' + OUTPUT_PATH +
                     ca_filename + '.mp4')

    # create file with date time info
    MY_LOGGER.debug('Writing out last generated date file')
    wxcutils.save_file(OUTPUT_PATH, ca_filename + '.txt', get_last_generated_text(ca_filename))


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
MODULE = 'find_files'
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


# try:

# check if find_files is already running, if so exit this code
if number_processes(MODULE + '.py') == 1:
    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-2]

    BASEDIR = '/home/pi/goes/'
    MY_LOGGER.debug('BASEDIR = %s', BASEDIR)

    SANCHEZ_PATH = BASEDIR + 'sanchez/'
    WEB_PATH = BASEDIR + 'web/'

    # load latest times data
    LATESTTIMESTAMPS = wxcutils.load_json(OUTPUT_PATH, 'goes_info.json')

    # load logo and branding info
    LOGOBLACK = cv2.imread(CONFIG_PATH + 'logo-black.jpg')
    LOGOWHITE = cv2.imread(CONFIG_PATH + 'logo-white.jpg')
    BRANDING = wxcutils.load_json(CONFIG_PATH, 'branding.json')

    # process GOES 16 files
    process_goes('16')

    # process GOES 15 files
    process_goes_2('15')

    # process Himawari 9 files
    process_himawari('9')

    # process GOES 18 files
    process_goes('18')

    # process GOES 17 files
    # do this one last of the image files so we've got the other
    # image files already loaded
    process_goes('17')

    # process nws files
    process_nws()

    # create animations
    # calculation = hours per day x frames per hour x number of days
    # create videos split over 3 hours
    # based on the value of the tens of minutes for the current time
    # this is to minimise the load on the server and the runtime for this code

    VIDEOS = wxcutils.load_json(CONFIG_PATH, 'videos.json')
    MY_LOGGER.debug('Number of videos = %d', len(VIDEOS))
    MY_LOGGER.debug('Number of hours = %d', math.ceil(len(VIDEOS) / 6))

    MIN_SECTION = math.floor(int(time.strftime('%M')) / 10)
    MY_LOGGER.debug('MIN_SECTION = %s', MIN_SECTION)
    HOUR_SECTION = int(time.strftime('%H')) % (math.ceil(len(VIDEOS) / 6))
    MY_LOGGER.debug('HOUR_SECTION = %s', HOUR_SECTION)
    VIDEO_NUM = MIN_SECTION + (HOUR_SECTION * 6)
    MY_LOGGER.debug('VIDEO_NUM = %s', VIDEO_NUM)

    COUNTER = 0
    for video in VIDEOS:
        if COUNTER == VIDEO_NUM:
            MY_LOGGER.debug('+=' * 40)
            MY_LOGGER.debug('Found video to create - %s - %s - %d frames per hour', video['sat'], video['description'], video['frames'])

            create_animation(video['sat'], video['location'], video['file match'] , 24 * 3 * video['frames'],
                             video['duration'], video['resolution'], video['selection'], video['min_size'], video['end frame'])
            MY_LOGGER.debug('+=' * 40)
        COUNTER += 1

    # save latest times data
    wxcutils.save_json(OUTPUT_PATH, 'goes_info.json', LATESTTIMESTAMPS)

    # rsync files to server
    wxcutils.run_cmd('rsync -rt ' + OUTPUT_PATH + ' mike@192.168.100.18:/home/mike/wxcapture/goes')

else:
    MY_LOGGER.debug('Another instance of find_files.py is already running')
    MY_LOGGER.debug('Skip running this instance to allow the existing one to complete')

# except:
#     MY_LOGGER.critical('Global exception handler: %s %s %s',
#                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
