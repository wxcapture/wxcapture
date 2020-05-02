#!/usr/bin/env python3
"""discord bot test"""


# import libraries
import os
from datetime import datetime
import discord
from dotenv import load_dotenv
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
MODULE = 'discord_test'
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


load_dotenv()

DISCORD_CONFIG = wxcutils.load_json(CONFIG_PATH, 'config-discord.json')

TOKEN = DISCORD_CONFIG['discord token']
SERVER = DISCORD_CONFIG['server']

guild = discord.Client()


@guild.event
async def on_ready():
    print('We have logged in as {0.user}'.format(guild))

@guild.event
async def on_message(message):
    if message.author == guild.user:
        return

    if message.content.startswith('!hello'):
        await message.channel.send('Hello ' + message.author.display_name + '!')

guild.run(TOKEN)


MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
