#!/usr/bin/env python3
"""Discoord webhook images"""


# import libraries
import os
import sys
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
import cv2
import wxcutils


def is_light(filename, threshold):
    """see if the image is not dark"""
    try:
        MY_LOGGER.debug('Reading file from URL')
        data = requests.get(URL_BASE + filename)
        MY_LOGGER.debug('Writing file')
        open(WORKING_PATH + filename, 'wb').write(data.content)

        MY_LOGGER.debug('Reading file')
        img = cv2.imread(WORKING_PATH + filename)
        mean_components = img.mean(axis=0).mean(axis=0)
        mean = (mean_components[0] + mean_components[1] + mean_components[2]) / 3
        MY_LOGGER.debug('mean = %f, threshold = %d', mean, threshold)

        MY_LOGGER.debug('Deleting file')
        wxcutils.run_cmd('rm ' + WORKING_PATH + filename)

        if mean > threshold:
            MY_LOGGER.debug('Light - %f', mean)
            return True
    except:
        MY_LOGGER.critical('is_light exception handler: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

    MY_LOGGER.debug('Dark')
    return False


def webhooks(w_config_path, w_config_file, w_site_config_file, w_imagesfile, w_satellite,
             w_location, w_colour, w_description):
    """send data to webhooks as configured"""
    MY_LOGGER.debug('webhooks called with %s %s %s %s %s %s %s %s',
                    w_config_path, w_config_file, w_site_config_file,
                    w_imagesfile, w_satellite,
                    w_location, w_colour, w_description)

    # convert w_colour from hex string to an int
    w_colour = int(w_colour, 16)

    w_config = wxcutils.load_json(w_config_path, w_config_file)
    w_site_config = wxcutils.load_json(w_config_path, w_site_config_file)

    MY_LOGGER.debug('Iterate through webhooks')
    for w_row in w_config['webhooks']:
        MY_LOGGER.debug('webhook last 3 chars = %s', w_row[len(w_row) - 3:])
        w_webhook = DiscordWebhook(url=w_row)

        # create embed object for webhook
        w_embed = DiscordEmbed(title=w_satellite, description=w_location, color=w_colour)

        # set image
        w_embed.set_image(url=w_imagesfile)

        # set footer
        w_embed.set_footer(text=w_config['footer'].replace('[SITE]', w_site_config['website']))

        # add fields to embed
        w_embed.add_embed_field(name='Satellite', value=':satellite_orbital:' + w_satellite)
        if w_description != '':
            w_embed.add_embed_field(name='Pass Description', value=w_description)

        # add embed object to webhook
        w_webhook.add_embed(w_embed)

        w_response = w_webhook.execute()
        MY_LOGGER.debug('response = %s', w_response)


def webhook(url, sat, image_desc):
    """webhook each image"""
    try:
        # webhook
        MY_LOGGER.debug('Webhooking pass %s %s %s', URL_BASE + url, sat, image_desc)
        try:
            webhooks(CONFIG_PATH, 'config-discord.json', 'config.json',
                     URL_BASE + url,
                     sat, 'Geostationary Image',
                     'ff0000',
                     image_desc)
        except:
            MY_LOGGER.critical('Discord exception handler: %s %s %s',
                               sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
    except:
        MY_LOGGER.critical('Global exception handler: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])


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
MODULE = 'discord'
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

URL_BASE = 'https://kiwiweather.com/goes/'
MY_LOGGER.debug('URL_BASE = %s', URL_BASE)
THRESHOLD = 5
MY_LOGGER.debug('THRESHOLD = %d', THRESHOLD)

# do each webhook
# GOES 17
webhook('goes_17_fd_fc-tn.jpg', 'GOES 17', 'Full colour')

IMAGE = 'goes_17_m1_fc-tn.jpg'
if is_light(IMAGE, THRESHOLD):
    MY_LOGGER.debug('%s is not dark, firing webhook', IMAGE)
    webhook(IMAGE, 'GOES 17', 'Full colour Meso Area 1')
else:
    MY_LOGGER.debug('%s is dark, use IR image instead?', IMAGE)
    IMAGE = 'goes_17_m1_ch07-tn.jpg'
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, firing webhook', IMAGE)
        webhook(IMAGE, 'GOES 17', 'Infra red Meso 1 (normally California)')

IMAGE = 'goes_17_m2_fc-tn.jpg'
if is_light(IMAGE, THRESHOLD):
    MY_LOGGER.debug('%s is not dark, firing webhook', IMAGE)
    webhook(IMAGE, 'GOES 17', 'Full colour Meso Area 2')
else:
    MY_LOGGER.debug('%s is dark, use IR image instead?', IMAGE)
    IMAGE = 'goes_17_m2_ch07-tn.jpg'
    if is_light(IMAGE, THRESHOLD):
        MY_LOGGER.debug('%s is not dark, firing webhook', IMAGE)
        webhook(IMAGE, 'GOES 17', 'Infra red Meso 2 (normally Alaska)')

# GOES 16
webhook('goes_16_fd_ch13_enhanced-tn.jpg', 'GOES 16',
        'Enhanced clean IR longwave band')

# Himawari 8
webhook('himawari_8_fd_IR-tn.jpg', 'Himawari 8', 'Infra red')
webhook('himawari_8_fd_VS-tn.jpg', 'Himawari 8', 'Visible band')


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
