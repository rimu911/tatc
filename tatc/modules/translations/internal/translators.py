from __future__ import annotations
from functools import cached_property, lru_cache
from tatc.modules.translations.internal.interfaces import LanguageTranslator, TranslationResult

import translators as ts


__CACHED_TRANSLATORS={}


def get_translator(translation_engine: str) -> GenericTranslator:
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

    def translate(self, text: str, target_language: str):
        translated_text = ts.translate_text(
            query_text=text,
            to_language=target_language,
            translator=self.translation_engine
        )
        return TranslationResult(
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

    def translate(self, text: str, target_language: str):
        result = ts.translate_text(
            query_text=text,
            to_language=target_language,
            translator=self.translation_engine,
            is_detail_result=True
        )
        data = result['data'][-2]
        return TranslationResult(
            detected_language=data[-2],
            translated_text=data[0][0][5][0][0]
        )


class BingTranslator(GenericTranslator):
    def __init__(self):
        super().__init__('bing')

    def translate(self, text: str, target_language: str):
        result = ts.translate_text(
            query_text=text,
            to_language=target_language,
            translator=self.translation_engine,
            is_detail_result=True
        )
        return TranslationResult(
            detected_language=result['detectedLanguage']['language'],
            translated_text=result['translations'][0]['text']
        )
