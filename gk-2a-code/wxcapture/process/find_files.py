#!/usr/bin/env python3
"""find files to migrate"""


# import libraries
import os
import glob
import time
import subprocess
import calendar
from datetime import datetime
import numpy as np
import cv2
import wxcutils


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
                process_count += 1
        MY_LOGGER.debug('%d process(es) are running', process_count)
        return process_count
    except:
        # note this should not be possible!
        MY_LOGGER.debug('%s is NOT running', process_name)
    MY_LOGGER.debug('%s is NOT running', process_name)
    return 0


def find_latest_directory(directory):
    """find latest directory in directory"""
    latest = 0
    for directories in os.listdir(directory):
        if int(directories) > latest:
            latest = int(directories)
    return str(latest)


def find_directories(directory):
    """find directories in directory"""
    directory_set = []
    for directories in os.listdir(directory):
        directory_set.append(directories)
    return directory_set


def crawl_images(ci_directory):
    """crawl directory structure for all images
    of the data type directory"""
    # start at base, get list of all dates
    date_directories = find_directories(base_dir)

    # go through the right directory, find the files
    for dir in date_directories:
        dir_dir = os.path.join(os.path.join(base_dir, dir), ci_directory)
        for file in glob.glob(os.path.join(dir_dir, '*.*')):
            bits = os.path.split(file)
            l_filename, l_extenstion = os.path.splitext(bits[1])
            sub_bits = l_filename.split('_')
            # IMG_FD_014_IR105_20200808_022006
            # only add the FD images to the index
            if len(sub_bits) == 6:
                # MY_LOGGER.debug('dir = %s, file = %s, ext = %s, date = %s, time = %s',
                #                 bits[0], l_filename, l_extenstion, sub_bits[4], sub_bits[5])
                FILES.append({'dir': bits[0], 'file': l_filename, 'ext': l_extenstion,
                              'datetime': sub_bits[4] + sub_bits[5]})


def find_latest_file(directory):
    """find latest file in directory based on last modified timestamp"""
    latest_timestamp = 0.0
    latest_filename = ''
    for filename in os.listdir(directory):
        if '_sanchez' not in filename:
            file_timestamp = os.path.getmtime(os.path.join(directory, filename))
            if file_timestamp > latest_timestamp:
                latest_filename = filename
                latest_timestamp = file_timestamp
    MY_LOGGER.debug('latest_filename = %s, latest_timestamp = %f',
                    latest_filename, latest_timestamp)
    return latest_filename


def clahe_process(cp_in_path, cp_in_file, cp_out_path, cp_out_file):
    """clahe process the file using OpenCV library"""
    def clahe(in_img):
        """do clahe create processing on image"""
        return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4)).apply(in_img)

    def do_clahe_img(in_img):
        """do clahe merge processing on image"""
        b_chn, g_chn, r_chn = cv2.split(in_img)
        return cv2.merge((clahe(b_chn), clahe(g_chn), clahe(r_chn)))

    MY_LOGGER.debug('clahe_process %s %s %s %s', cp_in_path, cp_in_file,
                    cp_out_path, cp_out_file)
    MY_LOGGER.debug('process image')
    cp_out_img = do_clahe_img(cv2.imread(cp_in_path + cp_in_file))
    MY_LOGGER.debug('write new image')
    cv2.imwrite(cp_out_path + cp_out_file, cp_out_img)
    MY_LOGGER.debug('write image complete')


def create_thumbnail(ct_directory, ct_extension):
    """create thumbnail of the image"""
    wxcutils.run_cmd('convert \"' + OUTPUT_PATH + ct_directory +
                     ct_extension +  '\" -resize 9999x500 ' +
                     OUTPUT_PATH + ct_directory + '-tn' + ct_extension)


def get_local_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def animate(a_directory, a_filename, a_extenstion, a_frames, a_suffix):
    """create animation file"""
    def add_txt(at_path, at_file, add_duration):
        """add text"""

        if add_duration:
            line = 'file \'' + at_path + '/' + at_file + '\'' + \
                os.linesep + 'duration 0.05' + os.linesep
        else:
            line = 'file \'' + at_path + '/' + at_file + '\'' + os.linesep
        return line

    MY_LOGGER.debug('directory = %s, filename = %s, extenstion = %s, frames = %d, suffix = %s',
                    a_directory, a_filename, a_extenstion, a_frames, a_suffix)
    a_files = len(FILES)
    if a_frames > a_files:
        a_frames = a_files
        MY_LOGGER.debug('Reduced frames to %d as not enough frames exist (max = %d)',
                        a_frames, a_files)
    a_text = ''
    a_original_suffix = a_suffix

    MY_LOGGER.debug('Going throught the last %d frames', a_frames)
    if a_suffix != '':
        a_suffix = '_' + a_suffix + '_web'
    else:
        a_suffix = '_web'
    a_counter = a_files - a_frames
    while  a_counter < a_files:
        a_text = a_text + add_txt(FILES[a_counter]['dir'], FILES[a_counter]['file'] + a_suffix + FILES[a_counter]['ext'], True)
        a_counter += 1
    # add last frame again, but with no duration
    a_text += add_txt(FILES[a_files - 1]['dir'], FILES[a_files - 1]['file'] + a_suffix + FILES[a_files - 1]['ext'], False)

    # save as a file
    wxcutils.save_file(WORKING_PATH, 'framelist.txt', a_text)

    # create animation
    if a_original_suffix == '':
        a_suffix = 'raw'
    else:
        a_suffix = '_' + a_original_suffix

    wxcutils.run_cmd('ffmpeg -y -safe 0 -f concat -i ' + WORKING_PATH +
                     'framelist.txt -c:v libx264 -pix_fmt yuv420p -vf scale=800:800 ' + OUTPUT_PATH + 'FD-' +
                     a_suffix + '-' + str(a_frames) + '.mp4')

    # create file with date time info
    date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    wxcutils.save_file(OUTPUT_PATH, 'FD-' + a_suffix + '-' + str(a_frames) + '.txt', date_time)


def create_branded():
    """create branded images"""

    def add_kiwiweather():
        """add kiwiweather"""
        # Kiwiweather.com
        nonlocal image
        image = cv2.putText(image, 'Kiwi', (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)
        image = cv2.putText(image, 'Weather', (20, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)
        image = cv2.putText(image, '.com', (20, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)

    def add_logo(x_offset):
        """add logo"""
        # logo
        y_offset = 0
        nonlocal image
        image[y_offset:y_offset+logo.shape[0], x_offset:x_offset+logo.shape[1]] = logo


    def add_date(y_offset):
        """add date and time"""

        # date / time info
        bits = file['file'].split('_')
        year = bits[4][:4]
        month = calendar.month_abbr[int(bits[4][4:6])]
        day = bits[4][6:8]
        hour = bits[5][:2]
        min = bits[5][2:4]
        # MY_LOGGER.debug('year = %s, month = %s, day = %s, hour = %s min = %s', year, month, day, hour, min)
        nonlocal image
        image = cv2.putText(image, hour + ':' + min + ' UTC', (20, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)
        image = cv2.putText(image, day + '-' + month + '-' + year, (20, 80 + y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)

    def add_sat_info(x_offset, y_offset, satellite, process):
        """add satellite info"""

        nonlocal image
        image = cv2.putText(image, satellite, (x_offset, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)
        image = cv2.putText(image, process, (x_offset, 80 + y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 2, cv2.LINE_AA)

    MY_LOGGER.debug('create branded images where required')

    # load logo
    MY_LOGGER.debug('load logo')
    logo = cv2.imread(CONFIG_PATH + 'logo.jpg')

    for file in FILES:
            MY_LOGGER.debug('file = %s', file)

            # does raw branded file exist?
            if not os.path.exists(file['dir'] + '/' + file['file'] + '_web' + file['ext']):
                MY_LOGGER.debug('creating raw branded')
                # load raw image
                image = cv2.imread(file['dir'] + '/' + file['file'] + file['ext'])
                add_kiwiweather()
                add_logo(2000)
                add_date(2100)
                add_sat_info(1700, 2100, 'GK-2A', 'IR')
                # write out image
                cv2.imwrite(file['dir'] + '/' + file['file'] + '_web' + file['ext'], image)
            else:
                MY_LOGGER.debug('raw branded exists')

            # does sanchez file exist?
            if not os.path.exists(file['dir'] + '/' + file['file'] + '_sanchez' + file['ext']):
                MY_LOGGER.debug('creating sanchez')
                wxcutils.run_cmd('/home/pi/sanchez/Sanchez -u ' + CONFIG_PATH + 'world.2004' + str(datetime.now().month).zfill(2) +
                                '.3x5400x2700.jpg -s ' + file['dir'] + '/' + file['file'] + file['ext'] + \
                                '  -o ' + file['dir'] + '/' + file['file'] + '_sanchez' + file['ext'])
            else:
                MY_LOGGER.debug('sanchez exists')

            # does sanchez branded file exist?
            if not os.path.exists(file['dir'] + '/' + file['file'] + '_sanchez_web' + file['ext']):
                MY_LOGGER.debug('creating raw branded')
                # load raw image
                image = cv2.imread(file['dir'] + '/' + file['file'] + '_sanchez' + file['ext'])
                add_kiwiweather()
                add_logo(2512)
                add_date(2612)
                add_sat_info(2100, 2612, 'GK-2A', 'IR Sanchez')
                # write out image
                cv2.imwrite(file['dir'] + '/' + file['file'] + '_sanchez_web' + file['ext'], image)
            else:
                MY_LOGGER.debug('raw branded exists')


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
if number_processes('find_files.py') == 1:
    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date"). \
        decode('utf-8').split(' ')[-2]

    base_dir = '/home/pi/gk-2a/xrit-rx/received/LRIT/'
    MY_LOGGER.debug('base_dir = %s', base_dir)

    # load latest times data
    latest_timestamps = wxcutils.load_json(OUTPUT_PATH, 'gk2a_info.json')

    # find latest directory
    date_directory = find_latest_directory(base_dir)
    MY_LOGGER.debug('latest directory = %s', date_directory)

    date_base_dir = os.path.join(base_dir, date_directory)
    data_directories = find_directories(date_base_dir)

    # data store for files list
    # currently just for FD
    FILES = []

    # find latest file in each directory and copy to output directory
    for directory in data_directories:
        MY_LOGGER.debug('---------------------------------------------')
        MY_LOGGER.debug('directory = %s', directory)
        location = os.path.join(date_base_dir, directory)
        MY_LOGGER.debug('location = %s', location)
        latest_file = find_latest_file(location)
        MY_LOGGER.debug('latest_file = %s', latest_file)
        filename, extenstion = os.path.splitext(latest_file)
        MY_LOGGER.debug('extenstion = %s', extenstion)

        # date time for original file
        latest = os. path. getmtime(os.path.join(location, latest_file))
        MY_LOGGER.debug('latest = %d', latest)
        latest_local = wxcutils.epoch_to_local(latest, '%a %d %b %H:%M')
        MY_LOGGER.debug('latest_local = %s', latest_local)

        stored_timestamp = 0.0
        try:
            stored_timestamp = latest_timestamps[directory + extenstion]
        except NameError:
            pass
        except KeyError:
            pass

        # REMOVE REMOVE REMOVE
        # if directory == 'FD':
        #     stored_timestamp = 0

        MY_LOGGER.debug('stored_timestamp = %f, %f', stored_timestamp, latest)
        if stored_timestamp != int(latest):
            MY_LOGGER.debug('New %s file added, previous latest = %f, current latest = %f', directory, stored_timestamp, latest)
            latest_timestamps[directory + extenstion] = int(latest)
            date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'

            # additional processing of FD image
            if directory == 'FD':
                # crawl directories for all files
                crawl_images(directory)
                # sort
                FILES = sorted(FILES, key=lambda k: k['datetime'])
                # save to file system for debugging only
                # wxcutils.save_json(WORKING_PATH, 'crawl.json', FILES)

                # create branded images
                create_branded()

                # do the animations
                animate(directory, filename, extenstion, 143 * 3, '')
                animate(directory, filename, extenstion, 143 * 3, 'sanchez')

                wxcutils.save_file(OUTPUT_PATH, 'FD.txt', date_time)
                wxcutils.save_file(OUTPUT_PATH, 'clahe.txt', date_time)
                wxcutils.save_file(OUTPUT_PATH, 'FD_sanchez.txt', date_time)

                # sanchez processing
                # image will have been created during animation, so create thumbnail
                create_thumbnail('sanchez', extenstion)

                # copy latest files to the output directory
                wxcutils.copy_file(FILES[-1]['dir'] + '/' + FILES[-1]['file'] + '_web' + FILES[-1]['ext'],
                                   os.path.join(OUTPUT_PATH, directory + extenstion))
                wxcutils.copy_file(FILES[-1]['dir'] + '/' + FILES[-1]['file'] + '_sanchez_web' + FILES[-1]['ext'],
                                   os.path.join(OUTPUT_PATH, directory + '_sanchez' + extenstion))
                create_thumbnail(directory, extenstion)
                create_thumbnail(directory + '_sanchez', extenstion)

                # CLAHE processing of latest
                clahe_process(OUTPUT_PATH, 'FD.jpg', OUTPUT_PATH, 'clahe.jpg')
                create_thumbnail('clahe', extenstion)

            else:
                # copy file to the output directory
                wxcutils.copy_file(os.path.join(location, latest_file), os.path.join(OUTPUT_PATH, directory + extenstion))

                # create thumbnail
                if extenstion != '.txt':
                    create_thumbnail(directory, extenstion)

                # create file with date time info
                if directory != 'ANT':
                    wxcutils.save_file(OUTPUT_PATH, directory + '.txt', date_time)
                else:
                    wxcutils.save_file(OUTPUT_PATH, 'ANT.txt.txt', date_time)



        else:
            MY_LOGGER.debug('File unchanged')

    # save latest times data
    wxcutils.save_json(OUTPUT_PATH, 'gk2a_info.json', latest_timestamps)

    # rsync files to servers
    wxcutils.run_cmd('rsync -rt ' + OUTPUT_PATH + ' mike@192.168.100.18:/home/mike/wxcapture/gk-2a')
    wxcutils.run_cmd('rsync -rt ' + base_dir + ' --exclude *_sanchez* --exclude *web* pi@192.168.100.15:/home/pi/goes/gk-2a')

else:
    MY_LOGGER.debug('Another instance of find_files.py is already running')
    MY_LOGGER.debug('Skip running this instance to allow the existing one to complete')

# except:
#     MY_LOGGER.critical('Global exception handler: %s %s %s',
#                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
