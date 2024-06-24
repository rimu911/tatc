from __version__ import appname, version

from fast_langdetect import detect_langs
from twitchio import Message
from twitchio.ext import commands

from config.models import ChannelConfiguration
from errors import InvalidArgumentsError, UnauthorizedUserError
from utils.twitch import parse_twitch_emotes, sanitize_twitch_message
from utils import lists

import config
import translators as ts
import threading
import twitchio


class TwitchChatBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=config.twitch_access_token(),
            prefix='!'
        )
        self.__configurations = config.load_channels_configurations()
        self.__lock = threading.Lock()

    @property
    def configurations(self) -> dict[str, ChannelConfiguration]:
        return {key: ChannelConfiguration(value) for key, value in self.__configurations.items()}

    def get_configuration(self, channel_name: str):
        return ChannelConfiguration(self.__configurations.setdefault(channel_name, {}))

    def save_configurations(self):
        lock = self.__lock
        lock.acquire(blocking=True)
        try:
            config.save_channels_configurations(self.__configurations)
        finally:
            lock.release()

    async def event_ready(self):
        print(f'Logged successfully in as "{self.nick}".')
        channels = set()
        for channel, configuration in self.configurations.items():
            if configuration.enabled:
                channels.add(channel)

        channels.add(self.nick)
        channels_str = ', '.join([f'"{channel}"' for channel in channels])
        print(f'Joining {channels_str}...')
        await self.join_channels(list(channels))
        print('Done...')

    async def event_message(self, message: Message) -> None:
        if message.echo:
            return
        configuration = self.get_configuration(message.channel.name)

        try:
            await super().event_message(message)
            content = message.content

            if content.startswith(self._prefix):
                return

            emotes = parse_twitch_emotes(message.tags.get('emotes', ''))
            text = sanitize_twitch_message(
                content,
                emotes=emotes,
                remove_emojis=configuration.remove_emojis,
                remove_usernames=configuration.remove_usernames
            )

            if not len(text) or text in configuration.ignore_words:
                return

            detected_language = detect_langs(text, low_memory=config.low_memory_mode()).lower()
            print(
                f'author="{message.author.name}" '
                f'detected="{detected_language}" '
                f'original_text="{content}" '
                f'sanitized_text="{text}"'
            )
            if detected_language in configuration.ignore_languages:
                return

            for target_language in configuration.target_languages:
                if detected_language.lower() == target_language.lower():
                    continue
                output = '{author_name}: {text}'.format(
                    author_name=message.author.name,
                    text=ts.translate_text(
                        query_text=text,
                        to_language=target_language,
                        translator=configuration.translation_engine
                    )
                )
                print(f'[{detected_language} -> {target_language}] {output}')
                await message.channel.send(f'[{detected_language}] {output}')
            return None

        except Exception as err:
            if configuration.debug_mode:
                await message.channel.send(f'Error: "{str(err)}"')
            raise

    async def check_is_admin(
        self,
        context: commands.Context,
        params: any,
        delimiter: str = None,
        user: twitchio.PartialUser = None,
        help_message: str = None
    ):
        configuration = self.get_configuration(context.channel.name)
        if user is None:
            user = context.author

        if user.name not in config.bot_administrators():
            message = f'"{user.name}" is not an authorized user.'
            await context.send(message)
            raise UnauthorizedUserError(message)

        if delimiter:
            params = lists.strip(params.split(delimiter), remove_blank=True, remove_duplicates=True)

        if not params:
            if configuration.debug_mode:
                await context.send(help_message)
            raise InvalidArgumentsError(help_message)

        return params

    @commands.command(name='join')
    async def join(self, context: commands.Context, channels: str = None, user: twitchio.PartialUser = None):
        channels = await self.check_is_admin(
            context=context,
            user=user,
            delimiter=',',
            help_message=f'Usage: "!join <channel_name>" | "!join <channel_name_one>,<channel_name_two>,..."',
            params=channels
        )
        for channel in channels:
            self.get_configuration(channel).enabled = True

        await self.join_channels(channels)
        self.save_configurations()

    @commands.command(name='leave')
    async def leave(self, context: commands.Context, channels: str = None, user: twitchio.PartialUser = None):
        channels = await self.part_channels(await self.check_is_admin(
            context=context,
            user=user,
            delimiter=',',
            help_message=f'Usage: "!leave <channel_name>" | "!leave <channel_name_one>,<channel_name_two>,..."',
            params=channels
        ))
        for channel in channels:
            self.get_configuration(channel).enabled = False

        await self.part_channels(channels)
        self.save_configurations()

    @commands.command(name='config')
    async def config(
        self,
        context: commands.Context,
        method: str = '',
        key: str = '',
        value: str = None,
        user: twitchio.PartialUser = None
    ):
        if user is None:
            user = context.author

        if not (user.is_broadcaster or user.is_mod):
            message = f'"{user.name}" is not an authorized user.'
            raise UnauthorizedUserError(message)

        configuration = self.get_configuration(context.channel.name)
        keys = [
            'translation_engine',
            'target_languages',
            'ignore_languages',
            'debug_mode',
            'remove_emojis',
            'ignore_words',
            'remove_usernames'
        ]
        messages = []
        method = method.lower()
        key = key.lower()

        match method:
            case 'set':
                if not value:
                    message = f'"<value>" cannot be empty.'
                    raise InvalidArgumentsError(message)
                match key:
                    case 'translation_engine':
                        configuration.translation_engine = value
                        value = configuration.translation_engine
                    case 'target_languages':
                        languages = list(ts.get_languages(translator=configuration.translation_engine).keys())
                        target_languages = lists.strip(
                            value.lower().split(','),
                            remove_blank=True,
                            remove_duplicates=True
                        )
                        values = []
                        for language in languages:
                            if language.lower() in target_languages:
                                values.append(language)

                        configuration.target_languages = values
                        value = ','.join(configuration.target_languages)
                    case 'ignore_languages':
                        configuration.ignore_languages = lists.strip(
                            value.lower().split(','),
                            remove_blank=True,
                            remove_duplicates=True
                        )
                        value = ','.join(configuration.ignore_languages)
                    case 'debug_mode':
                        configuration.debug_mode = (value.lower() == 'true')
                        value = str(configuration.debug_mode).lower()
                    case 'remove_emojis':
                        configuration.remove_emojis = (value.lower() == 'true')
                        value = str(configuration.remove_emojis).lower()
                    case 'ignore_words':
                        configuration.ignore_words = configuration.ignore_words.union(lists.strip(
                            value.lower().split(','),
                            remove_blank=True,
                            remove_duplicates=True
                        ))
                        value = ','.join(configuration.ignore_words)
                    case 'remove_usernames':
                        configuration.remove_usernames = (value.lower() == 'true')
                        value = str(configuration.remove_usernames).lower()
                    case _:
                        messages.append(f'Usage: "!config set [{"|".join(keys)}] <value>".')
                        messages.append(f'For additional information: "!config help set <key>"')
                if key in keys:
                    messages.append(f'{key} = "{value}"')
                self.save_configurations()
            case 'unset':
                match key:
                    case 'translation_engine':
                        configuration.translation_engine = None
                        value = configuration.translation_engine
                    case 'target_languages':
                        configuration.target_languages = []
                        value = configuration.target_languages
                    case 'ignore_languages':
                        configuration.ignore_languages = []
                        value = configuration.ignore_languages
                    case 'debug_mode':
                        configuration.debug_mode = None
                        value = str(configuration.debug_mode).lower()
                    case 'remove_emojis':
                        configuration.remove_emojis = None
                        value = str(configuration.remove_emojis).lower()
                    case 'ignore_words':
                        configuration.ignore_words = set()
                        value = configuration.ignore_words
                    case 'remove_usernames':
                        configuration.remove_usernames = None
                        value = str(configuration.remove_usernames).lower()
                    case _:
                        messages.append(f'Usage: "!config unset [{"|".join(keys)}]".')
                if key in keys:
                    messages.append(f'{key} = "{value or ""}"')
                self.save_configurations()
            case 'help':
                match key:
                    case 'set':
                        match value:
                            case 'translation_engine':
                                messages.append(f'Usage: "!config set translation_engine <engine>"')
                                for supported_engines in lists.split(ts.translators_pool, 10):
                                    messages.append(f'Supported Engines: {", ".join(supported_engines)}')
                            case 'target_languages':
                                messages.append(
                                    f'Usage: "!config set target_languages <language>" | '
                                    f'"!config set target_languages <language_one>,<language_two>,..."'
                                )
                                languages = list(ts.get_languages(translator=configuration.translation_engine).keys())
                                for supported_languages in lists.split(languages, size=15):
                                    messages.append(f'Supported Languages ({configuration.translation_engine}): {", ".join(supported_languages)}')
                            case 'ignore_languages':
                                messages.append(
                                    f'Usage: "!config set ignore_languages <language>" | '
                                    f'"!config set ignore_languages <language_one>,<language_two>,..."'
                                )
                                languages = list(ts.get_languages(translator=configuration.translation_engine).keys())
                                for supported_languages in lists.split(languages, size=15):
                                    messages.append(f'Available Languages: {", ".join(supported_languages)}')
                            case 'debug_mode':
                                messages.append(f'Usage: "!config set debug_mode <true|false>"')
                            case 'remove_emojis':
                                messages.append(f'Usage: "!config set remove_emojis <true|false>"')
                            case 'ignore_words':
                                messages.append(
                                    f'Usage: "!config set ignore_words <word>" | '
                                    f'"!config set ignore_words <word_one>,<word_two>,..."'
                                )
                            case 'remove_usernames':
                                messages.append(f'Usage: "!config set remove_usernames <true|false>"')
                            case _:
                                messages.append(f'Usage: "!config help set [{"|".join(keys)}]".')
                    case _:
                        messages.append(f'Usage: "!config help [set|unset|get|help] [{"|".join(keys)}] <value>"')
            case 'get':
                match key:
                    case 'translation_engine':
                        messages.append(f'translation_engine = "{configuration.translation_engine}"')
                    case 'target_languages':
                        messages.append(f'target_languages = "{",".join(configuration.target_languages)}"')
                    case 'ignore_languages':
                        messages.append(f'ignore_languages =  "{",".join(configuration.ignore_languages)}"')
                    case 'debug_mode':
                        messages.append(f'debug_mode = "{str(configuration.debug_mode).lower()}"')
                    case 'remove_emojis':
                        messages.append(f'remove_emojis = "{str(configuration.remove_emojis).lower()}"')
                    case 'ignore_words':
                        messages.append(f'ignore_words = "{",".join(configuration.ignore_words)}"')
                    case 'remove_usernames':
                        messages.append(f'remove_usernames = "{str(configuration.remove_usernames).lower()}"')
                    case _:
                        messages.append(f'Usage: "!config show [{"|".join(keys)}]".')
            case _:
                messages.append(f'Usage: !config [set|unset|get|help] <key> <value>')

        for message in messages:
            print(message)
            await context.send(message)

    @commands.command(name='version')
    async def version(self, context: commands.Context):
        version_information = f'{appname} ({version})'

        print(version_information)
        await context.send(version_information)
