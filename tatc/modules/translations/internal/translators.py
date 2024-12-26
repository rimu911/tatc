from __future__ import annotations
from functools import cached_property, lru_cache
from os import path

from tatc.core import *
from tatc.modules.translations.internal.interfaces import LanguageTranslator, TranslationResult
from tatc.modules.translations.constants import MORSE_CODE_LANGUAGE_ID, MORSE_CODE_ENGINE

import json
import re
import translators as ts


RESOURCES=path.join(working_directory(), 'resources')
MORSE_CODE_RESOURCE=path.join(RESOURCES, 'morse_code.json')

__CACHED_TRANSLATORS={}


def get_translator(translation_engine: str, detected_languages: list[str]) -> GenericTranslator:
    if MORSE_CODE_LANGUAGE_ID in detected_languages:
        return __CACHED_TRANSLATORS.setdefault(MORSE_CODE_ENGINE, MorseCodeTranslator())
    
    match (translation_engine):
        case 'google':
            return __CACHED_TRANSLATORS.setdefault('google', GoogleTranslator())
        case 'bing':
            return __CACHED_TRANSLATORS.setdefault('bing', BingTranslator())
        case _:
            return __CACHED_TRANSLATORS.setdefault(translation_engine, GenericTranslator(translation_engine))


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

    def translate(self, text: str, target_languages: list[str]) -> list[TranslationResult]:
        results = []
        for target_language in target_languages:
            translated_text = ts.translate_text(
                query_text=text,
                to_language=target_language,
                translator=self.translation_engine
            )
            results.append(TranslationResult(
                detected_language='',
                translated_text=translated_text
            ))
        return results

    @lru_cache(maxsize=1)
    @staticmethod
    def __supported_engines() -> list[str]:
        return ts.translators_pool


class GoogleTranslator(GenericTranslator):
    def __init__(self):
        super().__init__('google')

    def translate(self, text: str, target_languages: list[str]) -> list[TranslationResult]:
        results = []
        for target_language in target_languages:
            result = ts.translate_text(
                query_text=text,
                to_language=target_language,
                translator=self.translation_engine,
                is_detail_result=True
            )
            data = result['data'][-2]
            results.append(TranslationResult(
                detected_language=data[-2],
                translated_text=data[0][0][5][0][0]
            ))
        return results


class BingTranslator(GenericTranslator):
    def __init__(self):
        super().__init__('bing')

    def translate(self, text: str, target_languages: list[str]) -> list[TranslationResult]:
        results = []
        for target_language in target_languages:
            result = ts.translate_text(
                query_text=text,
                to_language=target_language,
                translator=self.translation_engine,
                is_detail_result=True
            )
            results.append(TranslationResult(
                detected_language=result['detectedLanguage']['language'],
                translated_text=result['translations'][0]['text']
            ))
        return results


class MorseCodeTranslator(GenericTranslator):
    def __init__(self):
        with open(MORSE_CODE_RESOURCE) as fd:
            self.__morse_codes = dict(json.load(fd))

    @property
    def morse_codes(self):
        return self.__morse_codes

    def translate(self, text: str, target_languages: list[str]) -> list[TranslationResult]:
        text = text.replace('・', '.')
        words = []
        for morse_word in re.split(r'\s{2}', text.strip()):
            characters = []
            for morse_char in re.split(r'\s', morse_word):
                characters.append(self.morse_codes.get(morse_char, ''))
            words.append(''.join(characters))
        return [TranslationResult(
            detected_language=MORSE_CODE_LANGUAGE_ID,
            translated_text=' '.join(words)
        )]
