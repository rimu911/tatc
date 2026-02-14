from __future__ import annotations
from functools import cached_property
from os import environ
from typing import Union

from tatc.core.constants import *
from tatc.utilities import Boolean, String

import copy
import logging


class Environment:
    """
    The wrapper class to environment variables
    """
    @cached_property
    def __bot_administrators(self) -> set[str]:
        administrators = set([
            administrator.strip() for administrator in environ.get(BOT_ADMINISTRATORS, '').split(',')
        ])
        return administrators

    @cached_property
    def twitch_access_token(self) -> str:
        return environ.get(TWITCH_ACCESS_TOKEN)

    @property
    def bot_administrators(self) -> list[str]:
        return list(self.__bot_administrators).copy()

    @property
    def command_prefix(self) -> str:
        return environ.get(COMMAND_PREFIX, '!')

    @cached_property
    def logging_level(self) -> int:
        logging_level = environ.get(LOGGING_LEVEL, 'info').strip().lower()
        match logging_level:
            case 'debug':
                return logging.DEBUG
            case 'info':
                return logging.INFO
            case 'warn':
                return logging.WARNING
            case 'error':
                return logging.ERROR
            case 'critical':
                return logging.CRITICAL
            case _:
                return logging.FATAL


class TatcApplicationConfiguration:
    """
    The configuration object for TaTC
    """
    def __init__(self, data: dict[str, any]):
        self.__data = data

    @property
    def channels(self) -> list[str]:
        """
        Returns the channels associated to the current application
        """
        return list(self.__data.keys())

    def get_channel_configuration(self, channel: str) -> TatcChannelConfiguration:
        """
        Returns the per-channel configuration of the specified channel
        """
        return TatcChannelConfiguration(
            self.__data.setdefault(channel, {})
        )

    def to_dict(self) -> dict[str, any]:
        """
        Returns the dict version of the configuration
        """
        return copy.deepcopy(self.__data)


class TatcChannelConfiguration:
    """
    The configuration object for channels registered in TaTC
    """
    def __init__(self, data: dict[str, any]):
        self.__data = data

    @property
    def enabled(self) -> bool:
        """
        Returns true, when the bot should join the channel associated to the current configuration;
        otherwise, false.
        """
        return self.__data.setdefault(ENABLED, True)

    @property
    def debug_mode(self) -> bool:
        """
        Returns true, when errors message should be propagated as chat messages;
        Otherwise, false.
        """
        return self.__data.setdefault(DEBUG_MODE, False)

    @enabled.setter
    def enabled(self, value: bool | str | any):
        self.__data.setdefault(DEBUG_MODE, Boolean.parse(value))

    def get_module_configuration(self, __key: str, __type: type = None) -> dict[str, any] | any:
        data = self.__data.setdefault(__key, {})
        if __type:
            return __type(data)
        return data


class TatcModuleConfiguration:
    def __init__(self, name: str, channel_configuration: TatcChannelConfiguration):
        self.__name = name
        self.__data = channel_configuration.get_module_configuration(name)

    @property
    def data(self) -> dict[str, any]:
        return self.__data

    @property
    def name(self) -> str:
        return self.__name or ''

    @property
    def supported_keys(self) -> list[str]:
        raise NotImplementedError

    def get(self, __key):
        if __key not in self.supported_keys:
            raise KeyError(f'Unknown key: "{__key}"')
        value = self.__getattribute__(__key)
        if not isinstance(value, list):
            return value
        return ', '.join(String.try_split(value, ','))

    def set(self, __key: str, __value: Union[str, None]) -> str:
        value = self.__getattribute__(__key)
        is_list = isinstance(value, list)
        if is_list:
            __value = String.strips(
                String.try_split(__value, ',')
            )

        self.__setattr__(__key, __value)
        return self.get(__key)

    def info(self, __key: str) -> list[str]:
        raise NotImplementedError(f'Help not available for "{__key}"')
