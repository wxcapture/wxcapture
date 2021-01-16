#!/usr/bin/env python3
"""find files to migrate"""


# import libraries
import os
import time
import glob
import subprocess
import wxcutils


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
    return wxcutils.epoch_to_local(time.time(), '%a %d %b %H:%M')


def get_utc_date_time():
    """get the local date time"""
    return wxcutils.epoch_to_utc(time.time(), '%a %d %b %H:%M')


def create_thumbnail(ct_directory, ct_extension):
    """create thumbnail of the image"""
    wxcutils.run_cmd('convert \"' + OUTPUT_PATH + ct_directory + ct_extension +
                     '\" -resize 9999x500 ' + OUTPUT_PATH + ct_directory + '-tn' + ct_extension)


def do_sanchez(ds_src, ds_dest):
    """do sanchez processing on the image file"""
    MY_LOGGER.debug('Sanchez processing %s %s', ds_src, ds_dest)
    cmd = '/home/pi/sanchezFC/Sanchez reproject -s ' + ds_src + ' -o ' + ds_dest + ' -ULa -r 4 -f'
    MY_LOGGER.debug(cmd)
    wxcutils.run_cmd(cmd)
    MY_LOGGER.debug('Sanchez processing completed')


def process_goes(sat_num):
    """process GOES xx files"""

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

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(os.path.join(latest_dir, latest_file),
                                   os.path.join(OUTPUT_PATH, new_filename + extenstion))

                # create thumbnail
                create_thumbnail(new_filename, extenstion)

                 # create file with date time info
                date_time = 'Last generated at ' + get_local_date_time() + ' ' + \
                    LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
                wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', date_time)

                # update latest
                LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)

                # generate sanchezFC image if GOES17 and fc image
                if sat_num == '17' and channel_directory == 'fc' and type_directory == 'fd':
                    sanchez_dir = SANCHEZ_PATH + 'goes' + sat_num + '/' + 'fd/fc/'
                    # create directory (if needed)
                    mk_dir(sanchez_dir + latest_directory)
                    san_file_dir = sanchez_dir + latest_directory + '/'

                    # create sanchez image
                    do_sanchez(os.path.join(latest_dir, latest_file), san_file_dir + latest_file.replace('.jpg', '-sanchez.jpg'))

                    # copy to output directory
                    MY_LOGGER.debug('new_filename = %s', new_filename + '-sanchez')
                    wxcutils.copy_file(san_file_dir + latest_file.replace('.jpg', '-sanchez.jpg'),
                                       os.path.join(OUTPUT_PATH, new_filename + '-sanchez' + extenstion))

                    # create thumbnail
                    create_thumbnail(new_filename + '-sanchez', extenstion)

                    # create file with date time info
                    date_time = 'Last generated at ' + get_local_date_time() + ' ' + \
                        LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
                    wxcutils.save_file(OUTPUT_PATH, new_filename + '-sanchez' + '.txt', date_time)

                    # update latest
                    LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)              


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

            if stored_timestamp != int(latest):
                # new file found which hasn't yet been copied over

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(os.path.join(latest_dir, latest_file),
                                   os.path.join(OUTPUT_PATH,
                                                new_filename + extenstion))

                # create thumbnail
                create_thumbnail(new_filename, extenstion)

                 # create file with date time info
                date_time = 'Last generated at ' + get_local_date_time() + ' ' + \
                    LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
                wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', date_time)

                # update latest
                LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)

    MY_LOGGER.debug('---------------------------------------------')


def process_nws():
    """process nws files"""

    MY_LOGGER.debug('---------------------------------------------')
    MY_LOGGER.debug('NWS')

    # note that this code is a work around for an issue with goestools
    # https://github.com/pietern/goestools/issues/100
    # GOES nws directory / filenames are incorrect #100
    # once fixed, this code will need to be updated

    # move all nws files to the nwsall directory
    MY_LOGGER.debug('move new to nwsall directory')
    wxcutils.run_cmd('mv ' + BASEDIR + 'nws/*/ ' + BASEDIR + 'nwsall/')

    MY_LOGGER.debug('correctly rename files')
    # loop through all files in the directory and rename them to
    # remove the first, incorrect part of the filename
    # e.g. 19700101T000000Z_20201107060000-pacsfc72_latestBW.gif
    # to 20201107060000-pacsfc72_latestBW.gif
    for filename in os.listdir(BASEDIR + 'nwsall/'):
        if '.gif' in filename:
            MY_LOGGER.debug('filename = %s', filename)
            bits = filename.split('_')
            MY_LOGGER.debug('first bit = %s', bits[0])
            new_filename = filename[len(bits[0]) + 1:]
            MY_LOGGER.debug('new_filename = %s', new_filename)
            wxcutils.move_file(BASEDIR + 'nwsall/', filename, BASEDIR + 'nwsfixed/', new_filename)
        else:
            MY_LOGGER.debug('DELETE? = %s', filename)

    # now go through all images to find the latest of each type using filename
    graphic_types = ['EPAC_latest', 'GULF_latest', 'pac24_latestBW', 'pac48_latestBW',
                     'pac48per_latestBW', 'pacsfc24_latestBW', 'pacsfc48_latestBW',
                     'pacsfc72_latestBW', 'WATL_latest', 'pac48per_latestBW']
    for gtype in graphic_types:
        MY_LOGGER.debug('type = %s', gtype)
        latest_file = find_latest_filename_contains(BASEDIR + 'nwsfixed/', gtype)

        MY_LOGGER.debug('latest_file = %s', latest_file)

        # process if a file was found
        if latest_file:
            filename, extenstion = os.path.splitext(latest_file)
            new_filename = 'nws_' + gtype

            # see when last saved
            stored_timestamp = 0.0
            try:
                stored_timestamp = LATESTTIMESTAMPS[new_filename + extenstion]
            except NameError:
                pass
            except KeyError:
                pass

            # date time for original file
            latest = (int)(latest_file.split('-')[0])

            MY_LOGGER.debug('stored_timestamp = %f, latest = %f', stored_timestamp, latest)

            if stored_timestamp != int(latest):
                # new file found which hasn't yet been copied over

                # copy to output directory
                MY_LOGGER.debug('new_filename = %s', new_filename)
                wxcutils.copy_file(os.path.join(BASEDIR + 'nwsfixed/', latest_file),
                                   os.path.join(OUTPUT_PATH, new_filename + extenstion))

                # create thumbnail
                create_thumbnail(new_filename, extenstion)

                    # create file with date time info
                date_time = 'Last generated at ' + get_local_date_time() + ' ' + \
                    LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
                wxcutils.save_file(OUTPUT_PATH, new_filename + '.txt', date_time)

                # update latest
                LATESTTIMESTAMPS[new_filename + extenstion] = int(latest)

    MY_LOGGER.debug('copy to final folder based on filename')
    # now copy to the correct date folder based on the filename
    # eg filename = 20201203200046-pacsea_latestBW.gif
    MY_LOGGER.debug('using %s', BASEDIR + 'nwsfixed/*.gif')
    for nws_file in glob.glob(BASEDIR + 'nwsfixed/*.gif'):
        bits = os.path.split(nws_file)
        MY_LOGGER.debug('dir = %s, file = %s', bits[0], bits[1])
        if '.gif' in bits[1]:
            MY_LOGGER.debug('nws_file = %s, file name = %s, year = %s, month = %s, day = %s', nws_file, bits[1], bits[1][:4], bits[1][4:6], bits[1][6:8])
        # create directories, if needed
        mk_dir(BASEDIR + 'nwsdata/' + bits[1][:4])
        mk_dir(BASEDIR + 'nwsdata/' + bits[1][:4] + '/' + bits[1][4:6])
        mk_dir(BASEDIR + 'nwsdata/' + bits[1][:4] + '/' + bits[1][4:6] + '/' + bits[1][6:8])
        wxcutils.move_file(bits[0], bits[1], BASEDIR + 'nwsdata/' + bits[1][:4] + '/' + bits[1][4:6] + '/' + bits[1][6:8], bits[1])


    MY_LOGGER.debug('---------------------------------------------')


def create_animation(ca_directory, ca_file_match, ca_frames, ca_duration, ca_resolution):
    """create animation from images"""

    MY_LOGGER.debug('create_animation directory = %s, file_match = %s, frames = %s, duration = %s, resolution = %s',
                    ca_directory, ca_file_match, ca_frames, ca_duration, ca_resolution)

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
    ca_duration_text = 'duration ' + str(ca_duration) + os.linesep
    for ca_dir in ca_directories:
        # loop through files in each directory
        MY_LOGGER.debug('looking in %s', BASEDIR + ca_directory + '/' + ca_dir + '/' + ca_file_match)
        ca_frame_list = glob.glob(BASEDIR + ca_directory + '/' + ca_dir + '/' + ca_file_match)
        ca_frame_list.sort(reverse=True)
        # MY_LOGGER.debug('ca_frame_list = %s', ca_frame_list)
        for ca_line in ca_frame_list:
            ca_entry = 'file \'' + ca_line + '\'' + os.linesep
            if ca_frame_counter == 0:
                ca_text = ca_entry + ca_duration_text + ca_entry
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
    date_time = 'Last generated at ' + get_local_date_time() + ' ' + LOCAL_TIME_ZONE + ' [' + get_utc_date_time() + ' UTC].'
    wxcutils.save_file(OUTPUT_PATH, ca_filename + '.txt', date_time)


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
# get local time zone
LOCAL_TIME_ZONE = subprocess.check_output("date"). \
    decode('utf-8').split(' ')[-2]

BASEDIR = '/home/pi/goes/'
MY_LOGGER.debug('BASEDIR = %s', BASEDIR)

SANCHEZ_PATH = BASEDIR + 'sanchez/'

# load latest times data
LATESTTIMESTAMPS = wxcutils.load_json(OUTPUT_PATH, 'goes_info.json')

# process GOES 17 files
process_goes('17')

# process GOES 16 files
process_goes('16')

# process Himawari 8 files
process_himawari('8')

# process nws files
process_nws()

# create animations
# calculation = hours per day x frames per hour x number of days

# GOES 16 - ch 13 enhanced - 1 frame per hour
create_animation('goes16/fd/ch13_enhanced', '*', 24 * 1 * 3, 0.15, '800:800')

# GOES 17 - FD visible - 2 frames per hour
create_animation('goes17/fd/fc', '*', 24 * 2 * 3, 0.15, '800:800')

# ps -GOES 17 - FD visible Projected - 2 frames per hour
create_animation('sanchez/goes17/fd/fc', '*', 24 * 2 * 3, 0.15, '800:800')

# GOES 17 - M1 ch 7 IR shortwave - 4 frames per hour
create_animation('goes17/m1/ch07', '*', 24 * 4 * 3, 0.15, '800:800')

# GOES 17 - M2 ch 7 IR shortwave - 4 frames per hour
create_animation('goes17/m2/ch07', '*', 24 * 4 * 3, 0.15, '800:800')

# Himawari 8 - FD IR - 1 frame per hour
create_animation('himawari8/fd', '*FD_IR*', 24 * 1 * 3, 0.15, '800:800')

# save latest times data
wxcutils.save_json(OUTPUT_PATH, 'goes_info.json', LATESTTIMESTAMPS)

# rsync files to server
wxcutils.run_cmd('rsync -rt ' + OUTPUT_PATH + ' mike@192.168.100.18:/home/mike/wxcapture/goes')

# except:
#     MY_LOGGER.critical('Global exception handler: %s %s %s',
#                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
