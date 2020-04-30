#!/usr/bin/env python3
"""discord bot test"""


# import libraries
import os
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed
import wxcutils
import wxcutils_pi


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
MODULE = 'discord_webhook_test'
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

DISCORD_CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-discord.json')

webhook = DiscordWebhook(url=DISCORD_CONFIG['webhook'])

# create embed object for webhook
embed = DiscordEmbed(title='NOAA 19', description='Pass over Auckland, New Zealand', color=242424)

# set author
# embed.set_author(name='Author Name', url='author url', icon_url='author icon url')

# set image
embed.set_image(url='https://pbs.twimg.com/media/EW1RTp6U8AA4_fd?format=jpg&name=medium')

# set thumbnail
embed.set_thumbnail(url='https://pbs.twimg.com/media/EW1RTp6U8AA4_fd?format=jpg&name=small')

# set footer
embed.set_footer(text='WxCapture')

# set timestamp (default is now)
embed.set_timestamp()

# add fields to embed
embed.add_embed_field(name='Satellite', value=':satellite_orbital:NOAA 19')
embed.add_embed_field(name='Max Elevation', value='63°')
embed.add_embed_field(name='Duration', value='901 seconds')
embed.add_embed_field(name='Pass start', value='04:33:35 April 30 UTC')
embed.add_embed_field(name='Pass end', value='04:48:36 April 30 UTC')
embed.add_embed_field(name='Gain', value='28.8dB')

# add embed object to webhook
webhook.add_embed(embed)

response = webhook.execute()


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
