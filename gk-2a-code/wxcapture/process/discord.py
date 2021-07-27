#!/usr/bin/env python3
"""Discoord webhook Sanchez images"""


# import libraries
import os
import sys
from discord_webhook import DiscordWebhook, DiscordEmbed
import wxcutils


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


try:
    # webhook
    MY_LOGGER.debug('Webhooking pass')
    # files are ~ 2MB, so can tweet full size image
    DISCORD_IMAGE_URL = 'https://kiwiweather.com/gk-2a/sanchez.jpg'
    MY_LOGGER.debug('discord_image_url = %s', DISCORD_IMAGE_URL)
    try:
        webhooks(CONFIG_PATH, 'config-discord.json', 'config.json',
                 DISCORD_IMAGE_URL,
                 'GK-2A', 'Geostationary Image',
                 'ff0000',
                 'IR Image CLAHE-Sanchez processed')
    except:
        MY_LOGGER.critical('Discord exception handler: %s %s %s',
                           sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

except:
    MY_LOGGER.critical('Global exception handler: %s %s %s',
                       sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
