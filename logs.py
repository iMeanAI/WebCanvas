import logging
import os
import sys
import time
import colorlog
import re


log_folder = "LOGS"
if not os.path.exists(log_folder):
    os.makedirs(log_folder)
log_file_name = os.path.join(
    log_folder, time.strftime("%Y-%m-%d_%H-%M-%S") + ".log")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

stream_formatter = colorlog.ColoredFormatter(
    "%(asctime)s**[%(log_color)s%(levelname)s%(reset)s]**|| %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'INFO': 'green',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)


class Formatter(colorlog.ColoredFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.color_pattern = re.compile(r'\x1b\[[0-9;]*m')

    def format(self, record):
        formatted_record = super().format(record)
        clean_record = self.color_pattern.sub('', formatted_record)
        return clean_record


file_formatter = Formatter(
    "%(asctime)s**[%(levelname)s]**|| %(message)s",
    datefmt=None,
    reset=True,
    log_colors={
        'DEBUG': 'cyan',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'INFO': 'green',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)


file_handler = logging.FileHandler(log_file_name, encoding='utf-8')
file_handler.setFormatter(file_formatter)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(stream_formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
