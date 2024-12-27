
from dotenv import load_dotenv
from functools import lru_cache
from logging.handlers import *
from os import path

from twitchio.ext import commands

from tatc.core.configurations import *
from tatc.core.constants import *

import json
import logging
import os
import threading


load_dotenv(
    path.join(
        os.getcwd(), '.env'
    )
)

_LOCK_ = threading.Lock()
_CONFIG_FILE_NAME_ = 'channels.json'
_LOGGING_FORMAT_ = '%(levelname)8s:  %(message)s'


def working_directory() -> str:
    return os.path.abspath(
        os.getcwd()
    )


@lru_cache(maxsize=1)
def environment() -> Environment:
    return Environment()


@lru_cache(maxsize=1)
def init() -> TatcApplicationConfiguration:
    """
    Initializes the in-memory configuration from 'channels.json' if the file exists
    """
    file = os.path.join(working_directory(), _CONFIG_FILE_NAME_)
    data = {}
    if path.exists(file):
        with open(file, 'r') as fp:
            data.update(json.load(fp))

    return TatcApplicationConfiguration(data)


def sync_configuration():
    """
    Saves the in-memory configuration to 'channels.json'
    """
    lock = _LOCK_
    lock.acquire(blocking=True, timeout=5)
    try:
        configuration = init()
        with open(os.path.join(working_directory(), _CONFIG_FILE_NAME_), 'w') as fp:
            json.dump(configuration.to_dict(), fp, indent=2)
    finally:
        lock.release()


@lru_cache(maxsize=5)
def get_logger(logger_name: str):
    """
    Gets the logger of the specified name.
    """
    if not logger_name:
        logger_name = 'NULL'

    logger = logging.getLogger(logger_name)
    if logger.handlers:
        return logger

    handlers = [logging.StreamHandler()]
    match logger_name:
        case 'NULL':
            handlers.append(logging.NullHandler())
        case _:
            log_dir = path.join(working_directory(), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            file = path.join(log_dir, f'{logger_name}.log')
            handler = RotatingFileHandler(
                filename=file,
                maxBytes=10 * 1024 * 1024,
                delay=True,
                backupCount=5
            )
            if path.exists(file):
                handler.doRollover()
            handlers.append(handler)

    for handler in handlers:
        handler.setFormatter(logging.Formatter(fmt=_LOGGING_FORMAT_))
        logger.addHandler(handler)

    logger.setLevel(environment().logging_level)

    return logger


class TatcChannelModule(commands.Cog):
    """
    Represents a module that is used within a channel
    """
    def __init__(
        self,
        configuration: TatcApplicationConfiguration,
        name: str = None,
        logger: logging.Logger = None
    ):
        self.__configuration = configuration
        self.__name = name
        self.__logger = logger or get_logger('')
        self.__bot = None

    @property
    def bot(self) -> commands.Bot:
        return self.__bot

    @property
    def name(self) -> str:
        """
        The name of the channel
        """
        return self.__name or ''

    @property
    def _configurations(self) -> TatcApplicationConfiguration:
        return self.__configuration

    @bot.setter
    def bot(self, bot: commands.Bot):
        self.__bot = bot

    def get_module_configuration(self, channel_name: str) -> TatcModuleConfiguration:
        """
        Returns the configuration module object relevant to the current channel module
        """
        raise NotImplementedError

    @property
    def logger(self) -> logging.Logger:
        """
        Returns the logger associated with the current channel
        """
        return self.__logger

    async def cog_command_error(self, context: commands.Context, error: Exception) -> None:
        configuration = self._configurations.get_channel_configuration(context.channel.name)
        if configuration.debug_mode:
            await context.send(f'Error: "{str(error)}"')

        self.logger.error(str(error))
        self.logger.debug(error)
