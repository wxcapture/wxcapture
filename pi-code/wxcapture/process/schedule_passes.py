#!/usr/bin/env python3
"""Schedule satellite data collection
Also produce pass data for today plus the next few days
using configuration data"""

# import libraries
import os
import sys
import math
import subprocess
from subprocess import Popen, PIPE
import time
from datetime import datetime
from skyfield import api, almanac
from skyfield.api import Loader
import matplotlib
import matplotlib.pyplot as pyplot
import wxcutils


def is_daylight(id_pass_start, id_pass_end):
    """check if it is daylight at the time"""
    def get_timestamp(tmp_dt):
        part = tmp_dt.strftime('%Y-%m-%d-%H-%M')
        bits = part.split('-')
        return time_scale.utc(int(bits[0]), int(bits[1]), int(bits[2]), int(bits[3]), int(bits[4]))

    # if unable to load files, assume daylight is true
    # avoids crash and at worst will capture a nighttime pass
    try:

        # update planets info
        MY_LOGGER.debug('Loading new files')
        load = Loader(WORKING_PATH)
        time_scale = load.timescale()
        e_e = load('de421.bsp')

        start_time_epoch = float(wxcutils.local_datetime_to_epoch \
                    (datetime.today().replace(hour=0).replace(minute=0) \
                    .replace(second=0)))
        end_time_epoch = start_time_epoch + (24*60*60) - 1
        start_dt = wxcutils.epoch_to_datetime_utc(start_time_epoch)
        end_dt = wxcutils.epoch_to_datetime_utc(end_time_epoch)

        gps_location = api.Topos(CONFIG_INFO['GPS location NS'], CONFIG_INFO['GPS location EW'])

        a_t, a_y = almanac.find_discrete(get_timestamp(start_dt), get_timestamp(end_dt),
                                        almanac.sunrise_sunset(e_e, gps_location))
        MY_LOGGER.debug(a_t)
        MY_LOGGER.debug(a_y)

        daylight_start = wxcutils.utc_to_epoch(a_t[0].utc_iso().replace('T', ' ').replace('Z', ''),
                                            '%Y-%m-%d %H:%M:%S')
        daylight_end = wxcutils.utc_to_epoch(a_t[1].utc_iso().replace('T', ' ').replace('Z', ''),
                                            '%Y-%m-%d %H:%M:%S')

        # capture if middle of the pass is in daylight
        id_pass_midpoint = id_pass_start + ((id_pass_end - id_pass_start) / 2)
        MY_LOGGER.debug('daylight_start = %s, %s', daylight_start, wxcutils.epoch_to_local(daylight_start, '%a %d %b %H:%M'))
        MY_LOGGER.debug('daylight_end = %s, %s', daylight_end, wxcutils.epoch_to_local(daylight_end, '%a %d %b %H:%M'))
        MY_LOGGER.debug('id_pass_start = %s, %s', id_pass_start, wxcutils.epoch_to_local(id_pass_start, '%a %d %b %H:%M'))
        MY_LOGGER.debug('id_pass_midpoint = %s, %s', id_pass_midpoint, wxcutils.epoch_to_local(id_pass_midpoint, '%a %d %b %H:%M'))
        MY_LOGGER.debug('id_pass_end = %s, %s', id_pass_end, wxcutils.epoch_to_local(id_pass_end, '%a %d %b %H:%M'))

        MY_LOGGER.debug('twighlight allowance in minutes = %s', CONFIG_INFO['twilight allowance'])
        id_twighlight = float(CONFIG_INFO['twilight allowance']) * 60
        MY_LOGGER.debug('twighlight allowance in seconds = %f', id_twighlight)
 
        if (float(daylight_start) - id_twighlight) <= id_pass_midpoint <= (float(daylight_end) + id_twighlight) or \
            (float(daylight_start) - id_twighlight) <= id_pass_midpoint <= (float(daylight_end) + id_twighlight):
            MY_LOGGER.debug('This is a daylight pass')
            return 'Y'
        else:
            MY_LOGGER.debug('This is NOT a daylight pass')
    except:
        MY_LOGGER.debug('Exception during is_daylight: %s %s %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
        MY_LOGGER.debug('Assuming it is daylight so as to always capture a file in this case')
        return 'Y'
    return 'N'

def get_sdr_data(sdr_name):
    """extract SDR info"""
    MY_LOGGER.debug('get sdr data for %s', sdr_name)
    antenna = '???'
    chipset = '???'
    sdr_type = '???'
    centre_frequency = '???'
    frequency_range = '???'
    modules = '???'
    sdr_active = '???'
    serial_number = '???'
    bias_t = '???'

    sdr_data = wxcutils.load_json(CONFIG_PATH, 'sdr.json')

    for row in sdr_data['sdr']:
        MY_LOGGER.debug('L1 = %s', row)
        if row['name'] == sdr_name:
            antenna = row['antenna']
            chipset = row['chipset']
            sdr_type = row['sdr type']
            centre_frequency = row['centre frequency']
            frequency_range = row['frequency range']
            modules = row['modules']
            sdr_active = row['sdr active']
            serial_number = row['serial number']
            bias_t = row['bias t']

    MY_LOGGER.debug('%s %s %s %s %s %s %s %s %s', antenna, chipset, sdr_type,
                    centre_frequency, frequency_range, modules, sdr_active, serial_number, bias_t)
    return antenna, chipset, sdr_type, centre_frequency, frequency_range, modules, \
    sdr_active, serial_number, bias_t


def scheduler_command(sc_receive_code, sc_sat_name, sc_start_epoch,
                      sc_duration, sc_max_elevation):
    """create the command for the at scheduler"""
    MY_LOGGER.debug('sc_start_epoch = %s', sc_start_epoch)

    return 'echo \"' + sc_receive_code + ' ' + sc_sat_name + ' ' + \
                    str(sc_start_epoch) + ' ' + str(sc_duration) + ' ' + str(sc_max_elevation) + \
                    ' N \" |  at ' + EMAIL_OUTPUT + \
                    datetime.fromtimestamp(int(sc_start_epoch) - 60).strftime('%H:%M %D')


def get_predict(sat_data, sat, time_stamp, end_time_stamp, when, capture):
    """parse output from predict"""
    def date_value(row):
        """extract date time from row"""
        return row.split()[2][:2] + ' ' + \
            row.split()[2][2:5] + ' 20' + \
            row.split()[2][5:] + ' ' + row.split()[3]
    MY_LOGGER.debug('getting prediction between %s and %s', str(time_stamp),
                    str(end_time_stamp))

    # get the SDR data
    MY_LOGGER.debug('sat = %s', sat)
    antenna, chipset, sdr_type, centre_frequency, frequency_range, modules, \
    sdr_active, serial_number, bias_t = get_sdr_data(sat['sdr'])

    MY_LOGGER.debug('Grabbing prediction')
    sat_id = sat['NORAD catalog number']
    MY_LOGGER.debug('NORAD catalog number = %s', sat_id)
    MY_LOGGER.debug('Predict command: %s %s %s %s %s %s', '/usr/bin/predict', '-t',
                    WORKING_PATH + 'weather.tle', '-p', sat_id, str(time_stamp))

    cmd = Popen(['/usr/bin/predict', '-t', WORKING_PATH + 'weather.tle',
                 '-p', sat_id, str(time_stamp)]
                , stdout=PIPE, stderr=PIPE)
    stdout, stderr = cmd.communicate()
    MY_LOGGER.debug('stdout:%s', stdout)
    MY_LOGGER.debug('stderr:%s', stderr)

    lines = stdout.decode('utf-8').splitlines()

    lines_len = len(lines) - 1
    MY_LOGGER.debug('lines_len = %d', lines_len)
    if lines_len > 1:
        MY_LOGGER.debug('Prediction data = %s', lines)
    else:
        MY_LOGGER.critical('No prediction data - validate satellites.json and predict code'
                           ' - for satellite = %s', sat['name'])
    orbit = lines[0].split()[10]
    MY_LOGGER.debug('orbit = %s', orbit)

    MY_LOGGER.debug('Sat type = %s', sat['type'])
    elevation_type = 'Min Elevation-' + str(sat['type'])
    min_elevation = int(CONFIG_INFO[elevation_type])
    MY_LOGGER.debug('min_elevation = %s', str(min_elevation))

    # start to parse the predict output
    visible_start = ''
    visible_end = ''
    visible_at_start = False
    visible_at_end = False
    theta = []
    radius = []
    plot_labels = []

    if '+' in stdout.decode('utf-8'):
        visible = ''
        counter = 0
        for row in lines:
            elements = row.split()
            status = ''
            counter += 1
            try:
                status = elements[11].replace('*', VISIBLE_NO).replace('+', VISIBLE_YES).replace('0.000000', '_')
            except IndexError:
                status = '-'

            # capture if visible at the start of the pass
            if counter == 1 and status == VISIBLE_YES:
                visible_at_start = True

            # if visible and not yet started, start
            if status == VISIBLE_YES and visible_start == '':
                visible_start = date_value(row)

            # if not visible and has started, has not previously ended, end
            if status == VISIBLE_NO and visible_start != '' and visible_end == '':
                visible_end = date_value(row)

            # end of loop, so if started and not ended, end
            if visible_start != '' \
                and visible_end == '' \
                and counter == len(lines):
                visible_end = date_value(row)
                if  status == VISIBLE_YES:
                    visible_at_end = True

            # MY_LOGGER.debug(counter, len(lines), visible, visible_start, visible_end)
    else:
        visible = 'No'
    if visible != 'No':
        visible_duration = int(float(wxcutils.utc_to_epoch(visible_end, '%d %b %Y %H:%M:%S')) \
                               - float(wxcutils.utc_to_epoch(visible_start, '%d %b %Y %H:%M:%S')))
        MY_LOGGER.debug('visible_duration = %s', str(visible_duration))
        if visible_at_start and visible_at_end:
            visible = 'Yes - for all of pass'
        elif visible_at_start and not visible_at_end and visible_duration > 0:
            visible = 'Yes - for ' + str(visible_duration // 60) + ':' + \
            str(visible_duration % 60).zfill(2) + ' from start'
        elif not visible_at_start and visible_at_end and visible_duration > 0:
            visible = 'Yes - for ' + str(visible_duration // 60) + ':' + \
            str(visible_duration % 60).zfill(2) + ' from end'
        else:
            visible = 'No'
        MY_LOGGER.debug('visible = %s', visible)
        MY_LOGGER.debug('visible_start = %s', visible_start)
        MY_LOGGER.debug('visible_end = %s', visible_end)
    pass_start = lines[0].split()[1] + ' ' + lines[0].split()[2][:2] + \
        ' ' + lines[0].split()[2][2:5] + ' 20' + lines[0].split()[2][5:] + \
        ' ' + lines[0].split()[3]
    # MY_LOGGER.debug('pass start (UTC) = ' + pass_start)
    start_date_local = wxcutils.utc_to_local(pass_start, '%a %d %b %Y %H:%M:%S')
    # MY_LOGGER.debug('pass start (local) = ' + start_date_local)

    pass_end = lines[lines_len].split()[1] + ' ' + lines[lines_len].split()[2][:2] + ' ' + \
        lines[lines_len].split()[2][2:5] + ' 20' + lines[lines_len].split()[2][5:] + ' ' + \
        ' ' + lines[lines_len].split()[3]
    # MY_LOGGER.debug('pass end (UTC) = ' + pass_end)
    end_date_local = wxcutils.utc_to_local(pass_end, '%a %d %b %Y %H:%M:%S')
    # MY_LOGGER.debug('pass end (local) = ' + end_date_local)

    start_epoch = int(lines[0].split()[0])
    # MY_LOGGER.debug('start_epoch = ' + str(start_epoch))
    end_epoch = int(lines[lines_len].split()[0])
    # MY_LOGGER.debug('end_epoch = ' + str(end_epoch))

    duration = end_epoch - start_epoch
    # MY_LOGGER.debug('pass duration = ' + str(duration) + ' seconds')
    duration_string = str(duration // 60) + ':' + str(duration % 60).zfill(2)
    # MY_LOGGER.debug('pass duration = ' + duration_string)
    max_elevation = 0
    azimuthmax_elevation = 0

    for line in lines:
        elements = line.split()
        # MY_LOGGER.debug(elements)
        if int(elements[4]) > max_elevation:
            max_elevation = int(elements[4])
            azimuthmax_elevation = int(elements[5])
        # polar plot
        theta.append(-2 * math.pi * (float(elements[5]) - 90) / 360)
        radius.append((90 - float(elements[4])) / 90)
        plot_labels.append(wxcutils.epoch_to_local(elements[0], '%H:%M:%S'))

    MY_LOGGER.debug('max_elevation = %s', str(max_elevation))
    MY_LOGGER.debug('azimuthmax_elevation = %s', str(azimuthmax_elevation))
    if azimuthmax_elevation > 180:
        max_elevation_direction = 'W'
        max_elevation_direction_desc = 'West'
    else:
        max_elevation_direction = 'E'
        max_elevation_direction_desc = 'East'
    MY_LOGGER.debug('max_elevation_direction = %s', max_elevation_direction)

    MY_LOGGER.debug('predict first line = %s', lines[0])
    MY_LOGGER.debug('predict last line = %s', lines[lines_len])

    pass_radius_start = 1.0 - (float(lines[0].split()[4]) / 90.0)
    pass_radius_end = 1.0 - (float(lines[lines_len].split()[4]) / 90.0)
    pass_theta_start = (math.pi / 180.0) * float(lines[0].split()[5])
    pass_theta_end = (math.pi / 180.0) * float(lines[lines_len].split()[5])
    y_start = pass_radius_start * math.cos(pass_theta_start)
    y_end = pass_radius_end * math.cos(pass_theta_end)

    if y_start > y_end:
        MY_LOGGER.debug('Southbound pass')
        direction = 'Southbound'
    else:
        MY_LOGGER.debug('Northbound pass')
        direction = 'Northbound'

    plot_title = sat['name'] + '\n' + direction + ' Pass\n'

    capture_reason = 'Not defined'
    if capture == 'no':
        capture_reason = 'Not configured for capture'

    # only append if elevation high enough and in the current local day
    if (max_elevation >= min_elevation) and (start_epoch < end_time_stamp):

        # schedule pass
        # only schedule for today
        scheduler = ''
        receive_code = '???'
        if (when == 'today') and (capture == 'yes'):
            capture_reason = 'Capture criteria met'
            if sat['type'] == 'NOAA':
                receive_code = CODE_PATH + 'receive_noaa.py'
                scheduler = scheduler_command(receive_code, sat['name'],
                                              start_epoch, duration,
                                              max_elevation)
            # for Meteor, always record daylight passes, conditionally record night passes
            elif sat['type'] == 'METEOR':
                receive_code = CODE_PATH + 'receive_meteor.py'
                if is_daylight(float(start_epoch), float(end_epoch)) == 'Y':
                    MY_LOGGER.debug('Daylight pass - %s', str(start_epoch))
                    scheduler = scheduler_command(receive_code, sat['name'],
                                                  start_epoch, duration,
                                                  max_elevation)
                elif sat['night'] == 'yes':
                    MY_LOGGER.debug('Night pass - %s', str(start_epoch))
                    scheduler = scheduler_command(receive_code, sat['name'],
                                                  start_epoch, duration,
                                                  max_elevation)
                else:
                    MY_LOGGER.debug('Not scheduled as sensor turned off')
                    MY_LOGGER.debug('Darkness pass - %s', str(start_epoch))
                    capture_reason = 'Darkness and using visible light sensor'
            elif sat['type'] == 'SSTV':
                receive_code = CODE_PATH + 'receive_sstv.py'
                scheduler = scheduler_command(receive_code, sat['name'].replace('(', '').replace(')', ''),
                                              start_epoch, duration,
                                              max_elevation)
            elif sat['type'] == 'AMSAT':
                receive_code = CODE_PATH + 'receive_amsat.py'
                scheduler = scheduler_command(receive_code, sat['name'],
                                              start_epoch, duration,
                                              max_elevation)
            elif sat['type'] == 'MORSE':
                receive_code = CODE_PATH + 'receive_morse.py'
                scheduler = scheduler_command(receive_code, sat['name'],
                                              start_epoch, duration,
                                              max_elevation)
            else:
                MY_LOGGER.debug('No processsing code for %s of type %s', sat['name'], sat['type'])

        if 'METEOR' in sat['name']:
            symbol_rate = sat['meteor symbol rate']
            mode = sat['meteor mode']
        else:
            symbol_rate = 'n/a'
            mode = 'n/a'

        MY_LOGGER.debug('start_date_local = %s', start_date_local)
        pass_meridian = 'am'
        if int(start_date_local.split(' ')[4].split(':')[0]) > 11:
            pass_meridian = 'pm'

        filename_base = wxcutils.epoch_to_utc(start_epoch, '%Y-%m-%d-%H-%M-%S') + \
            '-' + sat['name'].replace(' ', '_').replace('(', '').replace(')', '')

        sat_data.append({'time': start_epoch, 'satellite': sat['name'],
                         'max_elevation': max_elevation,
                         'start_date_local': start_date_local,
                         'end_date_local': end_date_local,
                         'startDate': pass_start, 'endDate': pass_end,
                         'duration_string': duration_string,
                         'duration': duration, 'frequency': sat['frequency'],
                         'orbit': orbit, 'direction': direction,
                         'visible': visible,
                         'max_elevation_direction': max_elevation_direction,
                         'max_elevation_direction_desc': max_elevation_direction_desc,
                         'scheduler': scheduler, 'capture': sat['capture'],
                         'receive code': receive_code,
                         'capture reason': capture_reason,
                         'theta': theta, 'radius': radius,
                         'plot_labels': plot_labels,
                         'plot_title': plot_title,
                         'filename_base': filename_base,
                         'priority': sat['priority'],
                         'meteor symbol rate': symbol_rate,
                         'meteor mode': mode,
                         'antenna': antenna,
                         'chipset': chipset,
                         'sdr': sat['sdr'],
                         'sdr type': sdr_type,
                         'centre frequency': centre_frequency,
                         'frequency range': frequency_range,
                         'modules': modules,
                         'sdr active': sdr_active,
                         'serial number': serial_number,
                         'bias t': bias_t,
                         'pass meridian': pass_meridian,
                         'sat type': sat['type']
                         })

    # return new start time for next pass search to start
    # 90 minutes for delay between passes (next orbit will be at least 90 minutes later)
    return end_epoch + (90*60)


def schedule(sat_data, sat, when, capture):
    """schedule each satellite"""
    MY_LOGGER.debug('---')
    MY_LOGGER.debug('Frequency = %s', str(sat['frequency']))
    MY_LOGGER.debug('Name = %s', sat['name'])

    if when == 'today':
        starttime_stamp = float(wxcutils.local_datetime_to_epoch \
            (datetime.today().replace(hour=0).replace(minute=0) \
            .replace(second=0)))
        end_time_stamp = starttime_stamp + (24*60*60) - 1
        MY_LOGGER.debug('today %s %s', str(starttime_stamp), str(end_time_stamp))
        MY_LOGGER.debug('Start = %s', wxcutils.epoch_to_local(starttime_stamp,
                                                              '%a %d %b %Y %H:%M:%S'))
        MY_LOGGER.debug('End = %s', wxcutils.epoch_to_local(end_time_stamp,
                                                            '%a %d %b %Y %H:%M:%S'))
    else:
        starttime_stamp = float(wxcutils.local_datetime_to_epoch \
            (datetime.today().replace(hour=0).replace(minute=0) \
            .replace(second=0))) + (24*60*60)
        end_time_stamp = starttime_stamp + \
            (int(CONFIG_INFO['Pass List Days']) * 24 * 60 * 60) - 1
        MY_LOGGER.debug('later %s %s', str(starttime_stamp), str(end_time_stamp))
        MY_LOGGER.debug('Start = %s', wxcutils.epoch_to_local(starttime_stamp,
                                                              '%a %d %b %Y %H:%M:%S'))
        MY_LOGGER.debug('End = %s', wxcutils.epoch_to_local(end_time_stamp,
                                                            '%a %d %b %Y %H:%M:%S'))
    MY_LOGGER.debug('looping through date range')
    while starttime_stamp < end_time_stamp:
        starttime_stamp = get_predict(sat_data, sat, starttime_stamp,
                                      end_time_stamp, when, capture)
        # MY_LOGGER.debug('new starttime_stamp = ' + str(starttime_stamp)


def remove_jobs(match):
    """remove old AT jobs"""
    text = subprocess.check_output('atq')
    lines = text.splitlines()
    MY_LOGGER.debug('lines = %s', lines)
    for line in lines:
        id_value = line.split()[0]
        MY_LOGGER.debug('  line = %s', line)
        MY_LOGGER.debug('  id_value = %s', id_value.decode('utf-8'))
        cmd = Popen(['/usr/bin/at', '-c', id_value.decode('utf-8')],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True)
        stdout, stderr = cmd.communicate()
        MY_LOGGER.debug('stdout:%s', stdout)
        MY_LOGGER.debug('stderr:%s', stderr)

        bits = stdout.split('}')
        if match in bits[1]:
            wxcutils.run_cmd('atrm ' + id_value.decode('utf-8'))


def migrate_files():
    """migrate files to server"""
    MY_LOGGER.debug('migrating files')
    files_to_copy = []
    files_to_copy.append({'source path': OUTPUT_PATH, 'source file': 'satpass.html', 'destination path': '', 'copied': 'no'})
    for sat in SAT_DATA:
        files_to_copy.append({'source path': IMAGE_PATH, 'source file': sat['filename_base'] + \
            '-plot.png', 'destination path': 'images/', 'copied': 'no'})
        files_to_copy.append({'source path': IMAGE_PATH, 'source file': sat['filename_base'] + '-plot-tn.png', 'destination path': 'images/', 'copied': 'no'})
    MY_LOGGER.debug('Files to copy = %s', files_to_copy)
    wxcutils.migrate_files(files_to_copy)
    MY_LOGGER.debug('Completed migrating files')


def process_overlaps():
    """remove passes where there is an overlap between satellites for the same SDR"""
    # overlap is where all the bullet points are true:
    # * both on same SDR
    # * end time of first is after start time of second
    # * start time of the first is before the start time of second


    def is_overlap(io_sat_a_start, io_sat_a_end, io_sat_b_start, io_sat_b_end):
        """test if there is an overlap between the two satellites"""
        # sdr buffer is to provide a buffer for the claim / release of the SDR between overlapping jobs
        # otherwise second pass will not be captured as the SDR is already in use
        # only testing where the start for sat B is between the start / end of sat A
        # otherwise would double process each overlap
        # end time for sat b is not currently used
        io_sdr_buffer = 1
        io_result = False
        if io_sat_a_start < io_sat_b_start < (io_sat_a_end + io_sdr_buffer):
            MY_LOGGER.debug('Sat B starts between the start and end of the pass for Sat A')
            io_result = True
        return io_result


    MY_LOGGER.debug('=' * 50)
    pass_adjust = int(CONFIG_INFO['Pass overlap threshold'])
    MY_LOGGER.debug('pass_adjust = %d', pass_adjust)
    for sat_a in SAT_DATA:
        for sat_b in SAT_DATA:
            # check that both are on the same SDR and both are currently scheduled
            # if not, there can't be a collision
            if sat_a['sdr'] == sat_b['sdr'] and sat_a['scheduler'] != '' and sat_b['scheduler'] != '':
                # potential overlap?
                if is_overlap(sat_a['time'], sat_a['time'] + sat_a['duration'], sat_b['time'], sat_b['time'] + sat_b['duration']):
                    MY_LOGGER.debug('Overlap to process between %s and %s', sat_a['satellite'], sat_b['satellite'])
                    MY_LOGGER.debug('Sat A %s start = %s, duration = %s, max ele = %s, priority = %s',
                                    sat_a['satellite'], str(sat_a['time']), str(sat_a['duration']),
                                    str(sat_a['max_elevation']), str(sat_a['priority']))
                    MY_LOGGER.debug('Sat B %s start = %s, duration = %s, max ele = %s, priority = %s',
                                    sat_b['satellite'], str(sat_b['time']), str(sat_b['duration']),
                                    str(sat_b['max_elevation']), str(sat_b['priority']))

                    # which to try to adjust, if can't determine, adjust A as a default
                    # priority tests
                    adjust = 'A'
                    if sat_a['priority'] > sat_b['priority']:
                        adjust = 'B'
                        MY_LOGGER.debug('Priority A > B')
                    elif sat_a['priority'] < sat_b['priority']:
                        adjust = 'A'
                        MY_LOGGER.debug('Priority B > A')
                    else:  # max elevation tests, since both equal priority
                        if sat_a['max_elevation'] > sat_b['max_elevation']:
                            adjust = 'B'
                            MY_LOGGER.debug('Max elevation A > B')
                        else:
                            adjust = 'A'
                            MY_LOGGER.debug('Max elevation B > A')

                    if adjust == 'A': # Trying to adjust A to avoid overlap
                        MY_LOGGER.debug('Trying to adjust A to avoid overlap')
                        # A is early, try adjust A end time
                        if not is_overlap(sat_a['time'], sat_a['time'] + sat_a['duration'] - pass_adjust,
                                          sat_b['time'], sat_b['time'] + sat_b['duration']):
                            MY_LOGGER.debug('Reduce end time for A will avoid overlap')
                            sat_a['capture reason'] = 'Capture criteria met with reduced end time to avoid overlap'
                            sat_a['duration'] = sat_a['duration'] - pass_adjust
                        else: # try adjust A end time and B start time
                            if not is_overlap(sat_a['time'], sat_a['time'] + sat_a['duration'] - pass_adjust,
                                              sat_b['time'] + pass_adjust, sat_b['time'] + sat_b['duration'] - pass_adjust):
                                MY_LOGGER.debug('Reduce end time for A and start time for B will avoid overlap')
                                sat_a['capture reason'] = 'Capture criteria met with reduced end time to avoid overlap'
                                sat_a['duration'] = sat_a['duration'] - pass_adjust
                                sat_a['capture reason'] = 'Capture criteria met with delayed start time to avoid overlap'
                                sat_b['time'] = sat_b['time'] + pass_adjust
                                sat_b['duration'] = sat_b['duration'] - pass_adjust
                            else:
                                MY_LOGGER.debug('Not able to avoid overlap, remove A')
                                sat_a['scheduler'] = ''
                                sat_a['capture reason'] = 'Overlapping passes not adjustable within threshold'

                    else: # Trying to adjust B to avoid overlap

                        MY_LOGGER.debug('Trying to adjust B to avoid overlap')
                        # A is early, try adjust B start time
                        if not is_overlap(sat_a['time'], sat_a['time'] + sat_a['duration'],
                                          sat_b['time'] + pass_adjust, sat_b['time'] + sat_b['duration'] - pass_adjust):
                            MY_LOGGER.debug('Increase start time for B will avoid overlap')
                            sat_b['capture reason'] = 'Capture criteria met with delayed start time to avoid overlap'
                            sat_b['time'] = sat_b['time'] + pass_adjust
                            sat_b['duration'] = sat_b['duration'] - pass_adjust
                        else: # try adjust A end time and B start time
                            if not is_overlap(sat_a['time'], sat_a['time'] + sat_a['duration'] - pass_adjust,
                                              sat_b['time'] + pass_adjust, sat_b['time'] + sat_b['duration'] - pass_adjust):
                                MY_LOGGER.debug('Reduce end time for A and start time for B will avoid overlap')
                                sat_a['capture reason'] = 'Capture criteria met with reduced end time to avoid overlap'
                                sat_b['capture reason'] = 'Capture criteria met with delayed start time to avoid overlap'
                                sat_b['time'] = sat_b['time'] + pass_adjust
                                sat_b['duration'] = sat_b['duration'] - pass_adjust
                            else:
                                MY_LOGGER.debug('Not able to avoid overlap, remove B')
                                sat_b['scheduler'] = ''
                                sat_b['capture reason'] = 'Overlapping passes - not adjustable within threshold'
                    # reschedule
                    if sat_a['scheduler'] != '':
                        sat_a['scheduler'] = scheduler_command(sat_a['receive code'], sat_a['satellite'],
                                                               sat_a['time'], sat_a['duration'],
                                                               sat_a['max_elevation'])
                    if sat_b['scheduler'] != '':
                        sat_b['scheduler'] = scheduler_command(sat_b['receive code'], sat_b['satellite'],
                                                               sat_b['time'], sat_b['duration'],
                                                               sat_b['max_elevation'])
                    MY_LOGGER.debug('')
    MY_LOGGER.debug('=' * 50)


def create_plot(sat_element):
    """create polar plot for satellite pass"""
    MY_LOGGER.debug('Creating plot for pass')
    return_value = ''
    try:
        MY_LOGGER.debug('Axes')
        pyplot.axes(polar=True)
        MY_LOGGER.debug('Title')
        pyplot.title(sat_element['plot_title'], fontsize=10)
        MY_LOGGER.debug('Plot data')
        pyplot.polar(sat_element['theta'], sat_element['radius'], linestyle='dashed', linewidth=2.5,
                     color='red', marker='+', markersize=10.0, markeredgecolor='blue')
        MY_LOGGER.debug('Plot labels')
        for (theta, radius, label) in zip(sat_element['theta'], sat_element['radius'],
                                          sat_element['plot_labels']):
            pyplot.text(theta, radius, '.......' + label, fontsize=6)
        MY_LOGGER.debug('Grid 1')
        pyplot.thetagrids([0, 90, 180, 270], labels=['E', 'N', 'W', 'S'])
        MY_LOGGER.debug('Angle labels')
        rgrid_angle = 22.5
        if sat_element['max_elevation_direction'] == 'E':
            rgrid_angle = 180 - rgrid_angle
        pyplot.rgrids((0.33, 0.66, 1.0), ('60', '30', '0'), angle=rgrid_angle)
        MY_LOGGER.debug('Creating image file')
        pyplot.savefig(IMAGE_PATH + sat_element['filename_base'] + '-plot.png', bbox_inches='tight')
        MY_LOGGER.debug('Created image file')
        pyplot.close()
        MY_LOGGER.debug('Plot created')
        MY_LOGGER.debug('Getting image size')
        cmd = Popen(['identify', '-format', '\"%hx%w\"', IMAGE_PATH,
                     sat_element['filename_base'] + '-plot.png'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = cmd.communicate()
        MY_LOGGER.debug('stdout:%s', stdout)
        MY_LOGGER.debug('stderr:%s', stderr)

        dimensions = stdout.decode('utf-8').replace('\"', '')
        MY_LOGGER.debug('Original image dimensions = %s', dimensions)
        MY_LOGGER.debug('Creating thumbnail')
        wxcutils.run_cmd('convert -define png:size=' + dimensions + ' ' + IMAGE_PATH +
                         sat_element['filename_base'] + '-plot.png -thumbnail ' +
                         CONFIG_INFO['plot thumbnail size'] + ' ' + IMAGE_PATH +
                         sat_element['filename_base'] + '-plot-tn.png')
        MY_LOGGER.debug('Thumbnail created')
        MY_LOGGER.debug('Creating link')

        date_parts = sat_element['filename_base'].split('-')
        image_filename = CONFIG_INFO['Link Base'] + date_parts[0] + '/' + date_parts[1] + \
            '/' + date_parts[2] + '/images/' + sat_element['filename_base'] + '-plot.png'
        thumb_filename = CONFIG_INFO['Link Base'] + date_parts[0] + '/' + date_parts[1] + \
            '/' + date_parts[2] + '/images/' + sat_element['filename_base'] + '-plot-tn.png'

        return_value = '<a class=\"example-image-link\" href=\"' + image_filename + \
            '\" data-lightbox=\"' + image_filename + '\"><img class=\"example-image\" src=\"' + \
            thumb_filename + '\" height=' + CONFIG_INFO['plot thumbnail size'].split('x')[1] + \
            ' width=' + CONFIG_INFO['plot thumbnail size'].split('x')[0] + \
            ' alt=\"polar plot\" /></a>'

        MY_LOGGER.debug('Link - %s', return_value)

    except:
        MY_LOGGER.debug('Exception during plot creation: %s %s %s',
                        sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
    return return_value


def reboot_handler(sleep_time):
    """reboot handler to pause for network active"""
    with open('/proc/uptime', 'r') as file:
        uptime_seconds = float(file.readline().split()[0])
    if uptime_seconds < 10:
        MY_LOGGER.debug('Reboot as uptime = %d, sleeping %d seconds',
                        uptime_seconds, sleep_time)
        time.sleep(sleep_time)
        MY_LOGGER.debug('Sleep completed')
    else:
        MY_LOGGER.debug('Normal scheduled run')


def get_time_element(gte_datetime):
    """strip out non-time element"""
    return gte_datetime.split(' ')[4]


def get_non_year_element(gte_datetime):
    """strip out non-time element"""
    return gte_datetime.split(' ')[0] + ' ' + wxcutils.ordinal(int(gte_datetime.split(' ')[1])) + \
        ' ' +  gte_datetime.split(' ')[2] + ' ' +  gte_datetime.split(' ')[4]


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
MODULE = 'schedule_passes'
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

# globals
VISIBLE_YES = '+'
VISIBLE_NO = '_'

# global try block to catch any exceptions
try:
    # load config
    MY_LOGGER.debug('Load config')
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    # load satellites
    MY_LOGGER.debug('Load satellites')
    SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'satellites.json')

    # load SDRs
    MY_LOGGER.debug('Load SDRs')
    SDR_INFO = wxcutils.load_json(CONFIG_PATH, 'sdr.json')

    # get local time zone
    MY_LOGGER.debug('Get Timezone')
    LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]
    MY_LOGGER.debug('LOCAL_TIME_ZONE = %s', LOCAL_TIME_ZONE)

    # reboot? sleep 60 seconds to enable all services to start
    MY_LOGGER.debug('Need to sleep post a reboot?')
    reboot_handler(60)

    # Remove all AT jobs for scheduler
    MY_LOGGER.debug('Remove any existing AT jobs')
    remove_jobs('receive_')

    # validate tle files exist
    MY_LOGGER.debug('Validate TLE files exist')
    wxcutils.validate_tle(WORKING_PATH)

    # check if we email at job output or not
    EMAIL_OUTPUT = ''
    if CONFIG_INFO['email receive output'] == 'no':
        EMAIL_OUTPUT = ' -M '
        MY_LOGGER.debug('email at job output disabled')
    else:
        MY_LOGGER.debug('email at job output enabled')

    # Schedule each satellite pass for today
    MY_LOGGER.debug('Schedule passes')
    SAT_DATA = []
    for key, value in SATELLITE_INFO.items():
        for si in SATELLITE_INFO[key]:
            if si['active'] == 'yes':
                MY_LOGGER.debug('-' * 20)
                MY_LOGGER.debug(si)
                schedule(SAT_DATA, si, 'today', si['capture'])

    # remove passes where there is an overlap
    MY_LOGGER.debug('Process overlaps')
    process_overlaps()

    # sort data
    MY_LOGGER.debug('Sort passes')
    SAT_DATA = sorted(SAT_DATA, key=lambda k: k['time'])

    # schedule
    MY_LOGGER.debug('AT scheduling')
    for elem in SAT_DATA:
        try:
            if elem['scheduler'] != '':
                if time.time() < elem['time']:
                    MY_LOGGER.debug('>>>>>>>> %s', elem['scheduler'])
                    wxcutils.run_cmd(elem['scheduler'])
                    elem['timezone'] = LOCAL_TIME_ZONE
                    wxcutils.save_json(OUTPUT_PATH, elem['filename_base'] + '.json', elem)
                else:
                    MY_LOGGER.debug('%s - not scheduled due to being in the past',
                                    elem['satellite'])
            else:
                MY_LOGGER.debug('%s removed - active but not being recorded', elem['satellite'])
        except ValueError:
            MY_LOGGER.debug('when must be at a time in the future, never in the past - can ignore')
    wxcutils.save_json(WORKING_PATH, 'passes_today.json', SAT_DATA)

    # find satellite pass for next few days
    MY_LOGGER.debug('Passes for the next few days')
    SAT_DATA_NEXT = []
    for key, value in SATELLITE_INFO.items():
        for si in SATELLITE_INFO[key]:
            if si['active'] == 'yes':
                # MY_LOGGER.debug('-' * 20)
                schedule(SAT_DATA_NEXT, si, 'later', si['capture'])

    # sort data
    MY_LOGGER.debug('Sort next few days passes')
    SAT_DATA_NEXT = sorted(SAT_DATA_NEXT, key=lambda k: k['time'])

    # output as html
    MY_LOGGER.debug('Build webpage')
    with open(OUTPUT_PATH + 'satpass.html', 'w') as html:
        # html header
        html.write('<!DOCTYPE html>')
        html.write('<html lang=\"en\"><head>'
                   '<meta charset=\"UTF-8\">'
                   '<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">'
                   '<meta name=\"description\" content=\"Predicted satellite pass times / dates for NOAA and Meteor weather satellite plus the International Space Station (ISS) and Amsat (Amateur Satellites)\">'
                   '<meta name=\"keywords\" content=\"' + CONFIG_INFO['webpage keywords'] + '\">'
                   '<meta name=\"author\" content=\"WxCapture\">'
                   '<title>Satellite Pass Predictions'
                   '</title>'
                   '<link rel=\"stylesheet\" href=\"css/styles.css\">'
                   '<link rel=\"stylesheet\" href=\"lightbox/css/lightbox.min.css\">'
                   '<link rel=\"shortcut icon\" type=\"image/png\" href=\"' + CONFIG_INFO['Link Base'] + 'favicon.png\"/>')
        html.write('</head>')
        html.write('<body onload=\"defaulthide()\">')
        if CONFIG_INFO['skip header and footer'] == 'no':
            html.write(wxcutils.load_file(CONFIG_PATH,
                                        'main-header.txt').replace('PAGE-TITLE',
                                                                    'Satellite Pass Predictions'))
        html.write('<section class=\"content-section container\">')

        MY_LOGGER.debug('Table for today')
        NOW_DAY = str(datetime.now().strftime('%A'))
        NOW_DAY_NUM = str(datetime.now().strftime(datetime.now().strftime('%d')))
        NOW_DAY_ORD = wxcutils.ordinal(int(NOW_DAY_NUM))
        NOW_MONTH = datetime.now().strftime(datetime.now().strftime('%B'))
        NOW_YEAR = str(datetime.now().strftime(datetime.now().strftime('%Y')))
        NOW = NOW_DAY + ' ' + NOW_DAY_ORD + ' ' + NOW_MONTH + ' ' + NOW_YEAR
        html.write('<h2 class=\"section-header\">Today Over ' + CONFIG_INFO['Location'] + ' - ' + NOW + '</h2>')
        html.write('<button onclick=\"hideshow()\" id=\"showhide\" class=\"showhidebutton\">Show instructions</button>')
        html.write('<div id=\"instructionsDiv\">')
        html.write('<h2 class=\"section-header\">Instructions</h2>')
        html.write('<ul>')
        html.write('<li>A satellite name which appears like <del>NOAA 15</del> '
                   'is not being captured, with the reason why given.</li>')
        html.write('<li>A highlighted row is one where the maximum elevation is high and should'
                   ' give a great image</li>')
        html.write('<li>The polar plot can be clicked on to see more detail of the pass.</li>')
        html.write('</ul>')
        html.write('</div>')
        html.write('<table>')
        html.write('<tr><th>Satellite</th><th>Max Elevation</th>'
                   '<th>Polar Plot</th><th>Pass'
                   'Start (' + LOCAL_TIME_ZONE + ')</th><th>Pass End (' +
                   LOCAL_TIME_ZONE + ')</th>')
        if CONFIG_INFO['Hide Detail'] != 'yes':
            html.write('<th>Pass Start (UTC)</th><th>Pass End (UTC)</th>')
        html.write('<th>Pass Duration (min:sec)</th>')
        if CONFIG_INFO['Hide Detail'] != 'yes':
            html.write('<th>Frequency (MHz)</th><th>Antenna</th><th>Direction</th>')
        html.write('<th>Visible to the Eye? (min:sec)</th>')
        if CONFIG_INFO['Hide Capturing'] != 'yes':
            html.write('<th>Capturing?</th>')
        html.write('</tr>')

        # iterate through list
        MY_LOGGER.debug('Iterating through satellites')
        for elem in SAT_DATA:
            MY_LOGGER.debug('Generating row')
            # generate plot and link
            plot_link = create_plot(elem)
            FONT_EFFECT_START = ''
            FONT_EFFECT_END = ''
            if elem['scheduler'] == '':
                FONT_EFFECT_START = '<del>'
                FONT_EFFECT_END = '</del>'
            if (elem['max_elevation'] >= \
                int(CONFIG_INFO['Pass Highlight Elevation'])) \
                and (elem['scheduler'] != ''):
                html.write('<tr class=\"row-highlight\">')
            else:
                html.write('<tr>')
            html.write('<td>' + FONT_EFFECT_START + elem['satellite'] +
                       FONT_EFFECT_END + '</td>')
            html.write('<td>' + str(elem['max_elevation']) + '&deg; ' + \
                elem['max_elevation_direction_desc'] + '</td>')
            html.write('<td>' + plot_link + '</td>')
            html.write('<td>' + get_time_element(elem['start_date_local']) + '</td>')
            html.write('<td>' + get_time_element(elem['end_date_local']) + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'yes':
                html.write('<td>' + elem['startDate'] + '</td>')
                html.write('<td>' + elem['endDate'] + '</td>')
            html.write('<td>' + elem['duration_string'] + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'yes':
                html.write('<td>' + str(elem['frequency']) + '</td>')
                html.write('<td>' + str(elem['antenna']) + '</td>')
                html.write('<td>' + elem['direction'] + '</td>')
            html.write('<td>' + elem['visible'] + '</td>')
            if CONFIG_INFO['Hide Capturing'] != 'yes':
                if elem['scheduler'] != '':
                    html.write('<td>Yes - ' + elem['capture reason'] + '</td>')
                else:
                    html.write('<td>No - ' + elem['capture reason'] + '</td>')
            html.write('</tr>')
            MY_LOGGER.debug('Row generated')
        html.write('</table>')

        MY_LOGGER.debug('Table for next %s days', CONFIG_INFO['Pass List Days'])
        # next few days
        html.write('<h2 class=\"section-header\">Over Next ' + CONFIG_INFO['Pass List Days'] +
                   ' Days Over ' + CONFIG_INFO['Location'] + '</h2>')
        html.write('<table>')
        if CONFIG_INFO['Hide Detail'] == 'yes':
            html.write('<tr><th>Satellite</th><th>Max Elevation</th>'
                       '<th>Pass Start (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass End (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass Duration (min:sec)</th>'
                       '<th>Visible to the Eye? (min:sec)</th></tr>\n')
        else:
            html.write('<tr><th>Satellite</th><th>Max Elevation (&deg;)</th>'
                       '<th>Pass Start (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass End (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass Start (UTC)</th><th>Pass '
                       'End (UTC)</th><th>Pass Duration (min:sec)</th>'
                       '<th>Frequency (MHz)</th><th>Antenna</th>'
                       '<th>Direction</th><th>Visible to the Eye? (min:sec)</th></tr>\n')
        # iterate through list
        for elem in SAT_DATA_NEXT:
            if (elem['max_elevation'] >= \
                int(CONFIG_INFO['Pass Highlight Elevation'])) \
                and (elem['scheduler'] != ''):
                html.write('<tr class=\"row-highlight\">')
            else:
                html.write('<tr>')
            html.write('<td>' + elem['satellite'] + '</td>')
            html.write('<td>' + str(elem['max_elevation']) + '&deg; ' +
                       elem['max_elevation_direction_desc'] + '</td>')
            html.write('<td>' + get_non_year_element(elem['start_date_local']) + '</td>')
            html.write('<td>' + get_non_year_element(elem['end_date_local']) + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'yes':
                html.write('<td>' + elem['startDate'] + '</td>')
                html.write('<td>' + elem['endDate'] + '</td>')
            html.write('<td>' + elem['duration_string'] + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'yes':
                html.write('<td>' + str(elem['frequency']) + '</td>')
                html.write('<td>' + str(elem['antenna']) + '</td>')
                html.write('<td>' + elem['direction'] + '</td>')
            html.write('<td>' + elem['visible'] + '</td>')
            html.write('</tr>')
        html.write('</table>')
        html.write('</section>')

        MY_LOGGER.debug('Footer')
        if CONFIG_INFO['skip header and footer'] == 'no':
            html.write('<footer class=\"main-footer\">')
            html.write('<p id=\"footer-text\">Pass Data last updated at <span class=\"time\">' +
                    time.strftime('%H:%M (' +
                                    subprocess.check_output("date").
                                    decode('utf-8').split(' ')[-2] +
                                    ')</span> on <span class=\"time\">%d/%m/%Y</span>') +
                    '.</p>')
            html.write('</footer>')

        html.write('<script src=\"lightbox/js/lightbox-plus-jquery.min.js\"></script>')
        html.write('<script>')
        html.write('function hideshow() {')
        html.write('  var x = document.getElementById(\"instructionsDiv\");')
        html.write('  if (x.style.display === \"none\") {')
        html.write('    x.style.display = \"block\";')
        html.write('   showhide.innerHTML = \"Hide instructions\";')
        html.write(' } else {')
        html.write('   x.style.display = \"none\";')
        html.write('   showhide.innerHTML = \"Show instructions\";')
        html.write(' }')
        html.write('}')
        html.write('function defaulthide() {')
        html.write('  var x = document.getElementById(\"instructionsDiv\");')
        html.write('  x.style.display = \"none\";')
        html.write('  showhide.innerHTML = \"Show instructions\";')
        html.write('}')
        html.write('</script>')
        html.write('</body></html>')
        html.close()

    # migrate files to destination
    MY_LOGGER.debug('migrate files')
    migrate_files()

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
