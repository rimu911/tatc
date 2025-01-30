from __future__ import annotations
from __version__ import *
from typing import Optional
from twitchio import Message
from twitchio.ext import commands

from tatc.core import TatcChannelModule, TatcApplicationConfiguration, environment, get_logger, sync_configuration
from tatc.errors import InvalidArgumentsError, UnauthorizedUserError, UnknownModuleError
from tatc.utilities import String

import logging
import twitchio


class TatcTwitchChatBot(commands.Bot):
    """
    The bot implementation
    """
    def __init__(
        self,
        configuration: TatcApplicationConfiguration,
        modules: list[TatcChannelModule] = None
    ):
        super().__init__(
            token=environment().twitch_access_token,
            prefix=environment().command_prefix
        )
        self.__logger = get_logger('bot')
        self.__configuration = configuration
        self.__modules = self.__init_modules(modules)

    @property
    def configurations(self) -> TatcApplicationConfiguration:
        """
        Returns the configuration object associated to the current application
        """
        return self.__configuration

    @property
    def prefix(self) -> str:
        """
        Returns the prefix that associated to the commands for the bots
        """
        return self._prefix

    @property
    def logger(self) -> logging.Logger:
        """
        Returns the logger associated to the current bot
        """
        return self.__logger

    def __init_modules(self, modules: list[TatcChannelModule]) -> dict[str, TatcChannelModule]:
        data = {}
        if not modules:
            return data

        for module in sorted(modules, key=lambda item: item.name):
            name = (module.name or f'module-{(len(data) + 1):02}').lower()
            data[name] = module
        return data

    def __is_roles(
        self,
        user: twitchio.Chatter,
        is_administrator: bool = False,
        is_broadcaster: bool = False,
        is_moderator: bool = False
    ):
        administrators = environment().bot_administrators
        return False if String.is_blank(user) else (
            (is_moderator and (user.is_mod or user.is_broadcaster or user.name in administrators)) or
            (is_broadcaster and (user.is_broadcaster or user.name in administrators)) or
            (is_administrator and user.name in administrators)
        )

    def __require_roles(
        self,
        user: twitchio.Chatter,
        is_administrator: bool = False,
        is_broadcaster: bool = False,
        is_moderator: bool = False
    ):
        if not self.__is_roles(user, is_administrator=is_administrator, is_broadcaster=is_broadcaster, is_moderator=is_moderator):
            username = '<unknown>' if String.is_blank(user) else user.name
            raise UnauthorizedUserError(f'"{username}" is not an authorized user.')
        
    async def event_raw_data(self, data: str):
        self.logger.debug(f'event_raw_data: "{data}" length: "{len(data)}" type: "{type(data).__name__}"')
        self.logger.debug(f'is_blank: "{String.is_blank(data)}"')
        if String.is_blank(data):
            # for some unknown reasons, twitchio is failing to reconnect after disconnection or receiving a blank raw data
            self.logger.debug('Blank message received! Signalling stop!')
            self.loop.call_soon_threadsafe(self.loop.stop)
            return
        return await super().event_raw_data(data)
    
    async def event_error(self, error: Exception, data: Optional[str] = None):
        self.logger.error(error)
        if data:
            self.logger.debug(f'event_error: "{data}"')
        return await super().event_error(error, data)

    async def event_ready(self):
        self.logger.info(f'Logged in successfully as "{self.nick}"...')
        channels = set()
        for channel in self.configurations.channels:
            channel_configuration = self.configurations.get_channel_configuration(channel)
            if channel_configuration.enabled:
                channels.add(channel)

        channels.add(self.nick)
        self.logger.info('Joining channels: {channels}'.format(
            channels=', '.join(f'"{channel}"' for channel in channels)
        ))
        await self.join_channels(list(channels))
        self.logger.info(f'{appname} ({version}) is ready!')

        for module in self.__modules.values():
            module.bot = self
            self.add_cog(module)
            self.logger.info(f'Module loaded: "{module.name}"')

    async def event_command_error(self, context: commands.Context, error: Exception) -> None:
        configuration = self.configurations.get_channel_configuration(context.channel.name)
        if configuration.debug_mode or self.__is_roles(context.author, is_administrator=True):
            await context.send(f'Error: "{str(error)}"')

        self.logger.error(str(error))
        self.logger.debug(error)

    async def event_message(self, message: Message) -> None:
        self.logger.debug(f'message received -> {message.content}')
        return await super().event_message(message)

    @commands.command(name='join')
    async def join(self, context: commands.Context, channels: str = None, user: twitchio.Chatter = None):
        user = user or context.author
        self.__require_roles(user, is_administrator=True)

        channels = String.try_split(channels, delimiter=',')
        for channel in channels:
            channel_configuration = self.configurations.get_channel_configuration(channel)
            self.logger.debug(f'Enabling configuration for "{channel}"')
            channel_configuration.enabled = True

        text = ', '.join([f'"{channel}"' for channel in channels])
        self.logger.info(f'Joining channels: {text}')
        await self.join_channels(channels)

    @commands.command(name='leave')
    async def leave(self, context: commands.Context, channels: str = None, user: twitchio.Chatter = None):
        user = user or context.author
        if not channels:
            self.__require_roles(user, is_broadcaster=True)
            channels = [context.channel.name]
        else:
            self.__require_roles(user, is_administrator=True)

        channels = String.try_split(channels, delimiter=',')
        for channel in channels:
            self.logger.info(f'Leaving channel: {channel}')
            self.logger.debug(f'Disabling configuration for "{channel}"')
            self.configurations.get_channel_configuration(channel).enabled = False

        await self.part_channels(channels)

    @commands.command(name='config')
    async def config(
        self,
        context: commands.Context,
        module_name: str = '',
        method: str = '',
        key: str = '',
        value: str = None,
        user: twitchio.Chatter = None
    ):
        user = user or context.author
        self.__require_roles(user, is_moderator=True)

        module_name = module_name.lower()
        if module_name not in self.__modules.keys():
            raise UnknownModuleError(f'Error: Module "{module_name}" is unavailable')
        module = self.__modules[module_name]
        channel_module_configuration = module.get_module_configuration(context.channel.name)
        if channel_module_configuration is None:
            await context.send(f'Error: "{module_name}" is unavailable.')
            return
        
        if method == 'help' and not key:
            await context.send(f'Usage: "{self.prefix}config {module_name} [set|get|remove|help] <key> <value>"')
            return

        messages = []
        match method:
            case 'help':
                value = channel_module_configuration.get(key)
                value_str = '<value>'
                if isinstance(value, list):
                    value_str = f'[{value_str}|<value_one>,<value_two>,...]'

                messages.append(
                    f'Usage: "{self.prefix}config {module_name} [set|get|remove|info|help] {key}" {value_str}'
                )
            case 'set':
                new_value = channel_module_configuration.set(key, value)
                messages.append(f'{key} = "{new_value}"')
            case 'get':
                messages.append(f'{key} = "{channel_module_configuration.get(key)}"')
            case 'remove':
                messages.append(f'{key} = "{channel_module_configuration.set(key, None)}" (default)')
            case 'info':
                if key:
                    messages.extend(channel_module_configuration.info(key))
                else:
                    keys = ', '.join([f'"{k}"' for k in channel_module_configuration.supported_keys])
                    messages.append(f'Available keys: {keys}')
            case _:
                raise InvalidArgumentsError(f'Error: Method "{method}" is not a known method')

        for message in messages:
            self.logger.info(message)
            await context.send(message)

        sync_configuration()

    @commands.command(name='version')
    async def version(self, context: commands.Context, user: twitchio.Chatter = None):
        user = user or context.author
        self.__require_roles(user, is_moderator=True)

        await context.send(f'{appname} ({version})')
