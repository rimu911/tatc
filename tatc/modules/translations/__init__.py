from tatc.errors import ModuleNotEnabledError
from tatc.modules.translations.constants import *


from fast_langdetect import detect_langs
from twitchio import Message
from twitchio.ext import commands

from tatc.core import TatcChannelModule, TatcApplicationConfiguration, TatcChannelModuleConfiguration, get_logger
from tatc.modules.translations.configurations import TatcTranslationChannelModuleConfiguration, environment
from tatc.modules.translations.utilities import Twitch, TwitchEmote

import translators as ts


class TatcTranslationChannelModule(TatcChannelModule, commands.Cog):
    def __init__(
        self,
        configuration: TatcApplicationConfiguration,
    ):
        super().__init__(
            configuration=configuration,
            name=TRANSLATIONS,
            logger=get_logger(TRANSLATIONS)
        )

    def get_module_configuration(self, channel_name) -> TatcChannelModuleConfiguration:
        return TatcTranslationChannelModuleConfiguration(
            self._configurations.get_channel_configuration(channel_name)
        )

    @commands.Cog.event()
    async def event_message(self, message: Message):
        if message.echo:
            return

        if message.content.startswith(environment().command_prefix):
            return

        content = message.content
        channel_name = message.channel.name
        channel_module_configuration = TatcTranslationChannelModuleConfiguration(
            self._configurations.get_channel_configuration(channel_name)
        )
        if not channel_module_configuration.enabled:
            raise ModuleNotEnabledError(f'The module "{self.name}" is not enabled for "{channel_name}".')

        text = Twitch.sanitize_twitch_emotes(
            content,
            TwitchEmote.parse(message.tags.get('emotes', ''))
        )

        if channel_module_configuration.sanitize_emojis:
            text = Twitch.sanitize_emojis(text)

        if channel_module_configuration.sanitize_usernames:
            text = Twitch.sanitize_username(text)

        if not len(text) or text in channel_module_configuration.ignore_words:
            return

        detected_language = detect_langs(text, low_memory=environment().low_memory_mode).lower()
        self.logger.debug(
            f'author="{message.author.name}" '
            f'detected="{detected_language}" '
            f'original_text="{content}" '
            f'sanitized_text="{text}"'
        )
        if detected_language in channel_module_configuration.ignore_languages:
            return

        for target_language in channel_module_configuration.target_languages:
            if detected_language.lower() == target_language.lower():
                continue
            output = '{author}: {text}'.format(
                author=message.author.name,
                text=ts.translate_text(
                    query_text=text,
                    to_language=target_language,
                    translator=channel_module_configuration.translation_engine
                )
            )
            self.logger.info(f'[{detected_language} -> {target_language}] {output}')
            await message.channel.send(f'[{detected_language}] {output}')
