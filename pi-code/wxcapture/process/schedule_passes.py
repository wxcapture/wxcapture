#!/usr/bin/env python3
"""Schedule satellite data collection
Also produce pass data for today plus the next few days"""

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


# required to avoid display errors for pyplotlib
matplotlib.use('Agg')


def is_daylight(time_now):
    """check if it is daylight at the time"""
    def get_timestamp(tmp_dt):
        part = tmp_dt.strftime('%Y-%m-%d-%H-%M')
        bits = part.split('-')
        return time_scale.utc(int(bits[0]), int(bits[1]), int(bits[2]), int(bits[3]), int(bits[4]))

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

    daylight_start = wxcutils.utc_to_epoch(a_t[0].utc_iso().replace('T', ' ').replace('Z', ''),
                                           '%Y-%m-%d %H:%M:%S')
    daylight_end = wxcutils.utc_to_epoch(a_t[1].utc_iso().replace('T', ' ').replace('Z', ''),
                                         '%Y-%m-%d %H:%M:%S')

    if time_now < float(daylight_start) or time_now > float(daylight_end):
        return 'N'
    return 'Y'

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
    sdrs = SDR_INFO['sdr']
    for sdr_key, sdr_value in sdrs.items():
        MY_LOGGER.debug('key = %s value = %s', sdr_key, sdr_value)
        if sdr_key == sdr_name:
            antenna = sdrs[sdr_key]['antenna']
            chipset = sdrs[sdr_key]['chipset']
            sdr_type = sdrs[sdr_key]['sdr type']
            centre_frequency = sdrs[sdr_key]['centre frequency']
            frequency_range = sdrs[sdr_key]['frequency range']
            modules = sdrs[sdr_key]['modules']
            sdr_active = sdrs[sdr_key]['sdr active']
            serial_number = sdrs[sdr_key]['serial number']
    MY_LOGGER.debug('%s %s %s %s %s %s %s %s', antenna, chipset, sdr_type,
                    centre_frequency, frequency_range, modules, sdr_active, serial_number)
    return antenna, chipset, sdr_type, centre_frequency, frequency_range, modules, \
    sdr_active, serial_number


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
    sdr_active, serial_number = get_sdr_data(sat['sdr'])

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

    halfway = round(lines_len / 2)
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
            visible = visible + status

            if counter == 1 and status == VISIBLE_YES:
                visible_at_start = True

            # if visible and not yet started, start
            if status == VISIBLE_YES and visible_start == '':
                visible_start = date_value(row)

            # if not visible and has started, has not previously ended, end
            if status == VISIBLE_NO and visible_start != '' and visible_end == '':
                visible_end = date_value(row)

            if counter == halfway:
                visible = visible + '^'

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
        # MY_LOGGER.debug('Visible = ' + visible)
        # MY_LOGGER.debug('visible_start = ' + visible_start)
        # MY_LOGGER.debug('visible_end = ' + visible_end)
        visible_duration = int(float(wxcutils.utc_to_epoch(visible_end, '%d %b %Y %H:%M:%S')) \
                               - float(wxcutils.utc_to_epoch(visible_start, '%d %b %Y %H:%M:%S')))
        # MY_LOGGER.debug('visible_duration = ' + str(visible_duration))
        visible = visible + ' (' + str(visible_duration // 60) + ':' + \
            str(visible_duration % 60).zfill(2) + ')'
        if visible_at_start and visible_at_end:
            visible = 'Yes - for all of pass'
        elif visible_at_start and not visible_at_end:
            visible = 'Yes - for ' + str(visible_duration // 60) + ':' + \
            str(visible_duration % 60).zfill(2) + ' from start'
        elif not visible_at_start and visible_at_end:
            visible = 'Yes - for ' + str(visible_duration // 60) + ':' + \
            str(visible_duration % 60).zfill(2) + ' from end'
        MY_LOGGER.debug('visible = %s', visible)
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


    # MY_LOGGER.debug('max_elevation = ' + str(max_elevation))
    # MY_LOGGER.debug('azimuthmax_elevation = ' + str(azimuthmax_elevation))
    if azimuthmax_elevation > 180:
        max_elevation_direction = 'W'
    else:
        max_elevation_direction = 'E'
    # MY_LOGGER.debug('max_elevation_direction = ' + max_elevation_direction)

    # MY_LOGGER.debug(lines[0])
    # MY_LOGGER.debug(lines[lines_len])

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

    plot_title = direction + ' Pass\n'

    capture_reason = 'Not defined'
    if capture == 'no':
        capture_reason = 'Not configured for capture'

    # only append if elevation high enough and in the current local day
    if (max_elevation >= min_elevation) and (start_epoch < end_time_stamp):

        # schedule pass
        # only schedule for today
        scheduler = ''
        if (when == 'today') and (capture == 'yes'):
            capture_reason = 'Capture criteria met'
            if sat['type'] == 'NOAA':
                scheduler = 'echo \"' + CODE_PATH + 'receive_noaa.py ' + sat['name'] + ' ' + \
                    str(start_epoch) + ' ' + str(duration) + ' ' + str(max_elevation) + \
                    ' N \" |  at ' + EMAIL_OUTPUT + \
                    datetime.fromtimestamp(start_epoch).strftime('%H:%M %D')
            # for Meteor, always record daylight passes, conditionally record night passes
            elif sat['type'] == 'METEOR':
                if is_daylight(float(start_epoch)) == 'Y':
                    MY_LOGGER.debug('Daylight pass - %s', str(start_epoch))
                    scheduler = 'echo \"' + CODE_PATH + 'receive_meteor.py ' + \
                    sat['name'] + ' ' + str(start_epoch) + ' ' + \
                    str(duration) + ' ' + str(max_elevation) + \
                    ' N \" |  at ' + EMAIL_OUTPUT + \
                    datetime.fromtimestamp(start_epoch).strftime('%H:%M %D')
                elif sat['night'] == 'yes':
                    MY_LOGGER.debug('Night pass - %s', str(start_epoch))
                    scheduler = 'echo \"' + CODE_PATH + 'receive_meteor.py ' + \
                    sat['name'] + ' ' + str(start_epoch) + ' ' + \
                    str(duration) + ' ' + str(max_elevation) + \
                    ' N \" |  at ' + EMAIL_OUTPUT + \
                    datetime.fromtimestamp(start_epoch).strftime('%H:%M %D')
                else:
                    MY_LOGGER.debug('Not scheduled as sensor turned off')
                    MY_LOGGER.debug('Darkness pass - %s', str(start_epoch))
                    capture_reason = 'Darkness and using visible light sensor'
            elif sat['type'] == 'ISS':
                scheduler = 'echo \"' + CODE_PATH + 'receive_iss.py ' + \
                sat['name'].replace('(', '').replace(')', '') + ' ' + \
                str(start_epoch) + ' ' + \
                str(duration) + ' ' + str(max_elevation) + \
                ' N \" |  at ' + EMAIL_OUTPUT + \
                datetime.fromtimestamp(start_epoch).strftime('%H:%M %D')
            elif sat['type'] == 'AMSAT':
                scheduler = 'echo \"' + CODE_PATH + 'receive_amsat.py ' + \
                sat['name'].replace('(', '').replace(')', '').replace(' ', '_') + ' ' + \
                str(start_epoch) + ' ' + \
                str(duration) + ' ' + str(max_elevation) + \
                ' N \" |  at ' + EMAIL_OUTPUT + \
                datetime.fromtimestamp(start_epoch).strftime('%H:%M %D')
            else:
                MY_LOGGER.debug('No processsing code for %s of type %s', sat['name'], sat['type'])

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
                         'scheduler': scheduler, 'capture': sat['capture'],
                         'capture reason': capture_reason,
                         'theta': theta, 'radius': radius,
                         'plot_labels': plot_labels,
                         'plot_title': plot_title,
                         'filename_base': filename_base,
                         'priority': sat['priority'],
                         'antenna': antenna,
                         'chipset': chipset,
                         'sdr': sat['sdr'],
                         'sdr type': sdr_type,
                         'centre frequency': centre_frequency,
                         'frequency range': frequency_range,
                         'modules': modules,
                         'sdr active': sdr_active,
                         'serial number': serial_number
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
    for line in lines:
        id_value = line.split()[0]
        cmd = Popen(['/usr/bin/at', '-c', id_value.decode('utf-8')],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    universal_newlines=True)
        stdout, stderr = cmd.communicate()
        MY_LOGGER.debug('stdout:%s', stdout)
        MY_LOGGER.debug('stderr:%s', stderr)

        bits = stdout.split('}')
        if match in bits[1]:
            wxcutils.run_cmd('atrm ' + id_value.decode('utf-8'))


def scp_files():
    """scp files"""
    MY_LOGGER.debug('using scp')
    # load config
    scp_config = wxcutils.load_json(CONFIG_PATH, 'config-scp.json')
    wxcutils.run_cmd('scp ' + OUTPUT_PATH + 'satpass.html ' + scp_config['remote user'] + '@' + \
        scp_config['remote host'] + ':' + scp_config['remote directory'] + '/')
    for sat in SAT_DATA:
        wxcutils.run_cmd('scp ' + IMAGE_PATH + sat['filename_base'] + '-plot.png '
                         + scp_config['remote user']+ '@' + scp_config['remote host']
                         + ':' + scp_config['remote directory'] + '/images/')
        wxcutils.run_cmd('scp ' + IMAGE_PATH + sat['filename_base'] + '-plot-tn.png '
                         + scp_config['remote user']+ '@' + scp_config['remote host']
                         + ':' + scp_config['remote directory'] + '/images/')

def process_overlaps():
    """remove passes where there is an overlap between satellites for the same SDR"""
    # overlap is where all the bullet points are true:
    # * both on same SDR
    # * end time of first is after start time of second
    # * start time of the first is before the start time of second
    MY_LOGGER.debug('=' * 50)
    for sat_a in SAT_DATA:
        for sat_b in SAT_DATA:
            if ((sat_a['time'] + sat_a['duration']) > sat_b['time']) \
                and (sat_a['time'] < sat_b['time']) and \
                sat_a['sdr'] == sat_b['sdr']:
                MY_LOGGER.debug('Potential overlap to process........')
                MY_LOGGER.debug(sat_a['satellite'] + ' ' + sat_b['satellite'])
                MY_LOGGER.debug('>>>' + ' ' + sat_a['satellite'] + ' ' + str(sat_a['time']) + \
                    ' ' + str(sat_a['duration']) + ' ' + str(sat_a['max_elevation']) + ' ' + \
                    str(sat_a['priority']) + ' ' + sat_a['scheduler'])
                MY_LOGGER.debug('>>>' + ' ' + sat_b['satellite'] + ' ' + str(sat_b['time']) + \
                    ' ' + str(sat_b['duration']) + ' ' + str(sat_b['max_elevation']) + ' ' + \
                        str(sat_b['priority']) + ' ' + sat_b['scheduler'])

                # if either is not scheduled, confirm
                if sat_a['scheduler'] == '':
                    MY_LOGGER.debug('%s is not being scheduled', sat_a['satellite'])
                if sat_b['scheduler'] == '':
                    MY_LOGGER.debug('%s is not being scheduled', sat_b['satellite'])

                # both scheduled
                if sat_a['scheduler'] != '' and sat_b['scheduler'] != '':
                    # if one has the higher priority, keep that
                    if sat_a['priority'] > sat_b['priority']:
                        MY_LOGGER.debug('Removing %s since it has a lower priority',
                                        sat_b['satellite'])
                        sat_b['scheduler'] = ''
                        sat_b['capture reason'] = 'Lower priority than overlapping'
                    elif sat_a['priority'] < sat_b['priority']:
                        MY_LOGGER.debug('Removing %s since it has a lower priority',
                                        sat_a['satellite'])
                        sat_a['scheduler'] = ''
                        sat_a['capture reason'] = 'Lower priority than overlapping'
                    else:
                        # keep the one with the max elevation
                        MY_LOGGER.debug('Overlapping %s and %s', sat_a['satellite'],
                                        sat_b['satellite'])
                        MY_LOGGER.debug('max_elevation A = %d', sat_a['max_elevation'])
                        MY_LOGGER.debug('max_elevation B = %d', sat_b['max_elevation'])
                        if sat_a['max_elevation'] > sat_b['max_elevation']:
                            MY_LOGGER.debug('Removing %s based on maximum elevation',
                                            sat_b['satellite'])
                            sat_b['scheduler'] = ''
                            sat_b['capture reason'] = 'Lower elevation than overlapping'
                        else:
                            MY_LOGGER.debug('Removing %s based on maximum elevation',
                                            sat_a['satellite'])
                            sat_a['scheduler'] = ''
                            sat_a['capture reason'] = 'Lower elevation than overlapping'
                MY_LOGGER.debug('')
    MY_LOGGER.debug('=' * 50)


def create_plot(sat_element):
    """create polar plot for satellite data"""
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

# try block to catch any exceptions
try:
    # Echo $DISPLAY value to assist with troubleshooting X display issues
    DISPLAY = os.environ['DISPLAY']
    MY_LOGGER.debug('DISPLAY = %s', DISPLAY)

    # load config
    CONFIG_INFO = wxcutils.load_json(CONFIG_PATH, 'config.json')

    # load satellites
    SATELLITE_INFO = wxcutils.load_json(CONFIG_PATH, 'satellites.json')

    # load SDRs
    SDR_INFO = wxcutils.load_json(CONFIG_PATH, 'sdr.json')

    # get local time zone
    LOCAL_TIME_ZONE = subprocess.check_output("date").decode('utf-8').split(' ')[-2]

    # reboot? sleep 60 seconds to enable all services to start
    reboot_handler(60)

    # Remove all AT jobs for scheduler
    remove_jobs('receive_')

    # check if we email at job output or not
    EMAIL_OUTPUT = ''
    if CONFIG_INFO['email receive output'] == 'N':
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
    MY_LOGGER.debug('at scheduling')
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
                   '<title>Satellite Pass Predictions'
                   '</title>'
                   '<link rel=\"stylesheet\" href=\"css/styles.css\">'
                   '<link rel=\"stylesheet\" href=\"lightbox/css/lightbox.min.css\">'
                   '<link rel=\"shortcut icon\" type=\"image/png\" href=\"/wxcapture/favicon.png\"/>')
        html.write('</head>')
        html.write('<body onload=\"defaulthide()\">')
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
        html.write('<li>The visible number for a pass shows the number of minutes and seconds that the '
                   'pass is visible for, weather permitting.</li>')
        # html.write('<li>Visible ' +
        #            VISIBLE_NO + VISIBLE_NO + VISIBLE_NO + VISIBLE_NO + VISIBLE_NO + VISIBLE_NO + \
        #            '^' + \
        #            VISIBLE_YES + VISIBLE_YES + VISIBLE_YES + VISIBLE_YES + VISIBLE_YES + VISIBLE_YES + \
        #            ' means that the satellite pass, weather permitting, '
        #            'is not visble for the first half of the pass, with ^ being the pass mid-point '
        #            'and Y indicating where it is visible. The total time it may be visible from '
        #            'is shown in brackets, e.g. (4:51), being for 4 minutes and 51 seconds. </li>')
        html.write('</ul>')
        html.write('</div>')
        html.write(CONFIG_INFO['Pass Info'])
        html.write('<table>')
        if CONFIG_INFO['Hide Detail'] == 'Yes':
            html.write('<tr><th>Satellite</th><th>Max Elevation (&deg;)</th>'
                       '<th>Polar Plot</th><th>Pass'
                       'Start (' + LOCAL_TIME_ZONE + ')</th><th>Pass End (' +
                       LOCAL_TIME_ZONE + ')</th><th>Duration (min:sec)</th>'
                       '<th>Visible</th><th>Capturing?</th></tr>\n')
        else:
            html.write('<tr><th>Satellite</th><th>Max Elevation (&deg;)</th>'
                       '<th>Polar Plot</th><th>Pass'
                       'Start (' + LOCAL_TIME_ZONE + ')</th><th>Pass End (' +
                       LOCAL_TIME_ZONE + ')</th><th>Pass Start (UTC)</th><th>'
                       'Pass End (UTC)</th><th>Duration (min:sec)</th><th>'
                       'Frequency (MHz)</th><th>Antenna</th><th>Direction</th>'
                       '<th>Visible</th><th>Capturing?</th></tr>\n')
        # iterate through list
        MY_LOGGER.debug('Iterating through satellites')
        for elem in SAT_DATA:
            MY_LOGGER.debug('Generating row')
            # generate plot and link
            plot_link = create_plot(elem)
            row_colour = ''
            font_effect_start = ''
            font_effect_end = ''
            if elem['scheduler'] == '':
                font_effect_start = '<del>'
                font_effect_end = '</del>'
            if (elem['max_elevation'] >= \
                int(CONFIG_INFO['Pass Highlight Elevation'])) \
                and (elem['scheduler'] != ''):
                html.write('<tr class=\"row-highlight\">')
            else:
                html.write('<tr>')
            html.write('<td>' + font_effect_start + elem['satellite'] +
                       font_effect_end + '</td>')
            html.write('<td>' + str(elem['max_elevation']) + \
                elem['max_elevation_direction'] + '</td>')
            html.write('<td>' + plot_link + '</td>')
            html.write('<td>' + get_time_element(elem['start_date_local']) + '</td>')
            html.write('<td>' + get_time_element(elem['end_date_local']) + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'Yes':
                html.write('<td>' + elem['startDate'] + '</td>')
                html.write('<td>' + elem['endDate'] + '</td>')
            html.write('<td>' + elem['duration_string'] + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'Yes':
                html.write('<td>' + str(elem['frequency']) + '</td>')
                html.write('<td>' + str(elem['antenna']) + '</td>')
                html.write('<td>' + elem['direction'] + '</td>')
            html.write('<td>' + elem['visible'] + '</td>')
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
        if CONFIG_INFO['Hide Detail'] == 'Yes':
            html.write('<tr><th>Satellite</th><th>Max Elevation (&deg;)</th>'
                       '<th>Pass Start (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass End (' + LOCAL_TIME_ZONE +
                       ')</th><th>Duration (min:sec)</th>'
                       '<th>Visible</th></tr>\n')
        else:
            html.write('<tr><th>Satellite</th><th>Max Elevation (&deg;)</th>'
                       '<th>Pass Start (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass End (' + LOCAL_TIME_ZONE +
                       ')</th><th>Pass Start (UTC)</th><th>Pass '
                       'End (UTC)</th><th>Duration (min:sec)</th>'
                       '<th>Frequency (MHz)</th><th>Antenna</th>'
                       '<th>Direction</th><th>Visible</th></tr>\n')
        # iterate through list
        for elem in SAT_DATA_NEXT:
            rowColour = ''
            if (elem['max_elevation'] >= \
                int(CONFIG_INFO['Pass Highlight Elevation'])) \
                and (elem['scheduler'] != ''):
                html.write('<tr class=\"row-highlight\">')
            else:
                html.write('<tr>')
            html.write('<td>' + elem['satellite'] + '</td>')
            html.write('<td>' + str(elem['max_elevation']) +
                       elem['max_elevation_direction'] + '</td>')
            html.write('<td>' + elem['start_date_local'] + '</td>')
            html.write('<td>' + elem['end_date_local'] + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'Yes':
                html.write('<td>' + elem['startDate'] + '</td>')
                html.write('<td>' + elem['endDate'] + '</td>')
            html.write('<td>' + elem['duration_string'] + '</td>')
            if CONFIG_INFO['Hide Detail'] != 'Yes':
                html.write('<td>' + str(elem['frequency']) + '</td>')
                html.write('<td>' + str(elem['antenna']) + '</td>')
                html.write('<td>' + elem['direction'] + '</td>')
            html.write('<td>' + elem['visible'] + '</td>')
            html.write('</tr>')
        html.write('</table>')
        html.write('</section>')

        MY_LOGGER.debug('Footer')
        html.write('<footer class=\"main-footer\">')
        html.write('<p id=\"footer-text\">Pass Data last updated at <span class=\"time\">' +
                   time.strftime('%H:%M (' +
                                 subprocess.check_output("date").
                                 decode('utf-8').split(' ')[-2] +
                                 ')</span> on the <span class=\"time\">%d/%m/%Y</span>') +
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

    # acp file to destination
    MY_LOGGER.debug('SCP files')
    scp_files()

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
