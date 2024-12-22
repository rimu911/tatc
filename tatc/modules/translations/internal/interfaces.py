from __future__ import annotations

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
    
    def translate(self, text: str, target_language: str) -> TranslationResult:
        raise NotImplementedError


class TranslationResult:
    def __init__(
        self,
        detected_language: str,
        translated_text: str
    ):
        self.__detected_language = (detected_language or '').strip().lower()
        self.__translated_text = translated_text

    @property
    def detected_language(self):
        return self.__detected_language

    @property
    def translated_text(self):
        return self.__translated_text