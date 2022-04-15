#!/usr/bin/env python3
"""apply bandpass filter to .wav file"""

# import libraries
import os
import argparse
import numpy as np
from scipy.io.wavfile import write as wavwrite
from scipy.io.wavfile import read as wavread
from scipy.signal import butter, lfilter
import wxcutils


def parse_args():
    """parse command line arguments"""
    my_parser = argparse.ArgumentParser(description='Apply bandpass filter to a .wav file')
    my_parser.add_argument('Input',
                           metavar='in_file',
                           type=str,
                           help='the input file')
    my_parser.add_argument('Output',
                           metavar='out_file',
                           type=str,
                           help='the output file')
    my_parser.add_argument('Lower',
                           metavar='lower',
                           type=int,
                           help='the lower frequency')
    my_parser.add_argument('Upper',
                           metavar='upper',
                           type=int,
                           help='the upper frequency')
    return my_parser.parse_args()


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


def bandpass_filter(buffer):
    return butter_bandpass_filter(buffer, FREQ_LOWER, FREQ_HIGHER, FRAME_RATE, order=6)


# setup paths to directories
HOME = os.environ['HOME']
APP_PATH = HOME + '/wxcapture/'
CODE_PATH = APP_PATH + 'process/'
LOG_PATH = CODE_PATH + 'logs/'
OUTPUT_PATH = APP_PATH + 'output/'
IMAGE_PATH = OUTPUT_PATH + 'images/'
WORKING_PATH = CODE_PATH + 'working/'
CONFIG_PATH = CODE_PATH + 'config/'
AUDIO_PATH = APP_PATH + 'audio/'

# start logging
MODULE = 'bandpass'
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
MY_LOGGER.debug('AUDIO_PATH = %s', AUDIO_PATH)


ARGS = parse_args()

FILE_IN = ARGS.Input
FILE_OUT = ARGS.Output
FREQ_LOWER = ARGS.Lower
FREQ_HIGHER = ARGS.Upper

MY_LOGGER.debug('FILE_IN = %s', FILE_IN)
MY_LOGGER.debug('FILE_OUT = %s', FILE_OUT)
MY_LOGGER.debug('FREQ_LOWER = %s', FREQ_LOWER)
MY_LOGGER.debug('FREQ_HIGHER = %s', FREQ_HIGHER)

# read the file in
MY_LOGGER.debug('Reading %s', CODE_PATH + FILE_IN)
FRAME_RATE, data = wavread(CODE_PATH + FILE_IN)
MY_LOGGER.debug('FRAME_RATE = %dHz', FRAME_RATE)

# Filter the noisy signal.
MY_LOGGER.debug('Applying the filter')
filtered = np.apply_along_axis(bandpass_filter, 0, data).astype('int16')

# save the file out
MY_LOGGER.debug('Writing %s', CODE_PATH + FILE_OUT)
wavwrite(CODE_PATH + FILE_OUT, FRAME_RATE, filtered)

MY_LOGGER.debug('Execution end')
MY_LOGGER.debug('-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+')
