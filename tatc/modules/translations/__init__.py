from tatc.errors import ModuleNotEnabledError
from tatc.modules.translations.constants import *

from twitchio import Message
from twitchio.ext import commands

from tatc.core import TatcChannelModule, TatcApplicationConfiguration, TatcModuleConfiguration, get_logger
from tatc.modules.translations.configurations import TatcTranslationModuleConfiguration, environment
from tatc.modules.translations.internal.models import get_language_detection_model
from tatc.modules.translations.internal.translators import get_translator
from tatc.modules.translations.utilities import Twitch, TwitchEmote

import re


class TatcTranslationModule(TatcChannelModule, commands.Cog):
    def __init__(
        self,
        configuration: TatcApplicationConfiguration,
    ):
        super().__init__(
            configuration=configuration,
            name=TRANSLATIONS,
            logger=get_logger(TRANSLATIONS)
        )

    def get_module_configuration(self, channel_name) -> TatcTranslationModuleConfiguration:
        return TatcTranslationModuleConfiguration(
            self._configurations.get_channel_configuration(channel_name)
        )

    @commands.Cog.event()
    async def event_message(self, message: Message):
        if message.echo or (self.bot.nick == message.author.name and re.match(f'^\[.+?\] {self.nick}: .+$', message.content)):
            return

        if message.content.startswith(environment().command_prefix):
            return

        content = message.content
        channel_name = message.channel.name
        configuration = self.get_module_configuration(channel_name)
        if not configuration.enabled:
            raise ModuleNotEnabledError(f'The module "{self.name}" is not enabled for "{channel_name}".')

        text = Twitch.sanitize_twitch_emotes(
            content,
            TwitchEmote.parse(message.tags.get('emotes', ''))
        )
        text = Twitch.sanitize_uris(text)

        if configuration.sanitize_emojis:
            text = Twitch.sanitize_emojis(text)

        if configuration.sanitize_usernames:
            text = Twitch.sanitize_username(text)

        if not len(text) or text in configuration.ignore_words:
            return

        models = get_language_detection_model(configuration.morse_code_support)
        results = models.detect(text)
        detected_languages = set()
        for source_language, score in results:
            if score >= environment().language_detection_threshold:
                detected_languages.add(source_language)

        self.logger.debug(
            f'[author="{message.author.name}" '
            f'detected="{", ".join(detected_languages)}" '
            f'original_text="{content}" '
            f'sanitized_text="{text}"]'
        )
        if detected_languages:
            for detected_language in detected_languages:
                if detected_language in configuration.ignore_languages:
                    return

        translation_engine = configuration.translation_engine
        target_languages = configuration.target_languages
        if configuration.morse_code_support and MORSE_CODE_LANGUAGE_ID in detected_languages:
            target_languages = [MORSE_CODE_DECODED_LANGUAGE_ID]

        translator = get_translator(translation_engine, configuration.morse_code_support)
        target_languages = list(filter(lambda target_language: target_language.lower() not in detected_languages, target_languages))

        for result in translator.translate(text, tuple(target_languages)):
            if result.detected_language:
                if result.detected_language not in detected_languages:
                    models.train(text, result.detected_language)

                if result.detected_language == result.expected_language or \
                    result.detected_language in configuration.ignore_languages:
                    continue

            output = '{author}: {text}'.format(
                author=message.author.name,
                text=result.translated_text
            )
            source_language = result.detected_language or ' ,'.join(detected_languages)
            self.logger.info(f'[{source_language} -> {result.expected_language}] {output}')

            if result.translated_text:
                await message.channel.send(f'[{source_language}] {output}')
