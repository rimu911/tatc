from __future__ import annotations
from functools import lru_cache
from collections.abc import Iterator
from functools import cached_property, lru_cache
from os import path

from tatc.core import *
from tatc.modules.translations.internal.interfaces import LanguageTranslator, TranslationResult
from tatc.modules.translations.constants import MORSE_CODE_LANGUAGE_ID, MORSE_CODE_DECODED_LANGUAGE_ID

import json
import re
import translators as ts


RESOURCES=path.join(working_directory(), 'resources')
MORSE_CODE_RESOURCE=path.join(RESOURCES, 'morse_code.json')


@lru_cache()
def get_translator(translation_engine: str, morse_code_support: bool) -> LanguageTranslator:
    translator = None
    match (translation_engine):
        case 'google':
            translator = GoogleTranslator()
        case 'bing':
            translator = BingTranslator()
        case _:
            translator = GenericTranslator(translation_engine)

    return MorseCodeTranslator(translator) if morse_code_support else translator


class GenericTranslator(LanguageTranslator):
    def __init__(self, translation_engine: str):
        self.__translation_engine = translation_engine

    @property
    def supported_engines(self) -> list[str]:
        return self.__supported_engines()

    @cached_property
    def supported_languages(self) -> list[str]:
        return ts.get_languages(self.translation_engine)

    @property
    def translation_engine(self):
        return self.__translation_engine

    def translate(self, text: str, *target_languages: str) -> Iterator[TranslationResult]:
        for target_language in target_languages:
            translated_text = ts.translate_text(
                query_text=text,
                to_language=target_language,
                translator=self.translation_engine
            )
            yield TranslationResult(
                expected_language=target_language,
                detected_language='',
                translated_text=translated_text
            )

    @lru_cache(maxsize=1)
    @staticmethod
    def __supported_engines() -> list[str]:
        return ts.translators_pool


class GoogleTranslator(GenericTranslator):
    def __init__(self):
        super().__init__('google')

    def translate(self, text: str, *target_languages: str) -> Iterator[TranslationResult]:
        for target_language in target_languages:
            result = ts.translate_text(
                query_text=text,
                to_language=target_language,
                translator=self.translation_engine,
                is_detail_result=True
            )
            data = result['data'][-2]
            yield TranslationResult(
                expected_language=target_language,
                detected_language=data[-2],
                translated_text=data[0][0][5][0][0]
            )


class BingTranslator(GenericTranslator):
    def __init__(self):
        super().__init__('bing')

    def translate(self, text: str, *target_languages: str) -> Iterator[TranslationResult]:
        for target_language in target_languages:
            result = ts.translate_text(
                query_text=text,
                to_language=target_language,
                translator=self.translation_engine,
                is_detail_result=True
            )
            yield TranslationResult(
                expected_language=target_language,
                detected_language=result['detectedLanguage']['language'],
                translated_text=result['translations'][0]['text']
            )


class MorseCodeTranslator(LanguageTranslator):
    def __init__(self, translator: LanguageTranslator):
        self.__translator = translator
        self.__morse_codes = MorseCodeTranslator.get_morse_codes()

    @property
    def translator(self) -> LanguageTranslator:
        return self.__translator

    @property
    def morse_codes(self):
        return self.__morse_codes

    @property
    def supported_engines(self):
        return self.translator.supported_engines

    @property
    def supported_languages(self) -> list[str]:
        return self.translator.supported_languages

    def translate(self, text: str, *target_languages: str) -> Iterator[TranslationResult]:
        if MORSE_CODE_DECODED_LANGUAGE_ID in target_languages:
            text = text.replace('・', '.').replace('－', '-')
            words = []
            for morse_word in re.split(r'\s{2}|/', text.strip()):
                characters = []
                for morse_char in re.split(r'\s', morse_word):
                    characters.append(self.morse_codes.get(morse_char, ''))
                words.append(''.join(characters))
            yield TranslationResult(
                expected_language=MORSE_CODE_DECODED_LANGUAGE_ID,
                detected_language=MORSE_CODE_LANGUAGE_ID,
                translated_text=' '.join(words)
            )

        target_languages = filter(lambda target_language: target_language.lower() != MORSE_CODE_DECODED_LANGUAGE_ID, target_languages)
        for result in self.translator.translate(text, *target_languages):
            yield result

    @lru_cache(maxsize=1)
    @staticmethod
    def get_morse_codes() -> dict[str, str]:
        with open(MORSE_CODE_RESOURCE) as fd:
            return dict(json.load(fd))
