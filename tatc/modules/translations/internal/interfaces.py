from __future__ import annotations
from collections.abc import Iterator


class LanguageDetectionModel:
    def detect(text: str) -> list[(str, float)]:
        raise NotImplementedError
    
    def train(text: str, expected_language: str):
        raise NotImplementedError


class LanguageTranslator:
    @property
    def supported_engines(self) -> list[str]:
        raise NotImplementedError
    
    @property
    def supported_languages(self) -> list[str]:
        raise NotImplementedError
    
    def translate(self, text: str, *target_languages: str) -> Iterator[TranslationResult]:
        raise NotImplementedError


class TranslationResult:
    def __init__(
        self,
        expected_language: str,
        detected_language: str,
        translated_text: str
    ):
        self.__expected_language = expected_language.lower()
        self.__detected_language = (detected_language or '').strip().lower()
        self.__translated_text = translated_text

    @property
    def expected_language(self) -> str:
        return self.__expected_language

    @property
    def detected_language(self) -> str:
        return self.__detected_language

    @property
    def translated_text(self) -> str:
        return self.__translated_text