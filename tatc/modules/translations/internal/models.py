from tatc.core import *
from tatc.modules.translations.configurations import environment
from tatc.modules.translations.internal.interfaces import LanguageDetectionModel
from tatc.utilities import Directory, String

from functools import lru_cache
from lingua import Language, LanguageDetector, LanguageDetectorBuilder
from os import path
from pathlib import Path
from typing import Iterable

import csv
import re
import sqlite3
import threading


DATABASE_FILE=path.join(working_directory(), 'models.db')
RESOURCES=path.join(working_directory(), 'resources')


@lru_cache(maxsize=1)
def get_language_detection_model():
    model = environment().language_detection_model
    if model not in ['adaptive-forced'] and \
        environment().default_translation_engine not in ['google', 'bing']:
        model = 'legacy'
    
    logger = get_logger('models')
    logger.info(f'Language Detection Model Loaded: {model}')
    match model:
        case 'legacy':
            return LegacyDetectionModel()
        case 'legacy-lazy':
            return LazyLoadingDetectionModel(['en', 'ja', 'zh'])
        case 'adaptive' | 'adaptive-forced':
            return NaiveBayesDetectionModel()

    return None


class LanguageDetectionResult:
    def __init__(self, language_id: str, count: int, score: int, word_count: int):
        self.__language_id = language_id or ''
        self.__count = count or 0
        self.__score = score or 0
        self.__word_count = word_count
    
    @property
    def language_id(self):
        return self.__language_id
    
    @property
    def count(self):
        return self.__count
    
    @property
    def score(self):
        return self.__score / self.__word_count
    
    def __str__(self):
        return f'[language_id="{self.language_id}" count="{self.count}" score="{self.score}"]'


class NaiveBayesDetectionModel(LanguageDetectionModel):
    def __init__(self):
        super().__init__()
        self.__pattern = re.compile(r'[\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]|[\w]+')
        self.__logger = get_logger('models')
        self.__init__database(self.connection)
    
    @property
    def logger(self):
        return self.__logger

    def __init__database(self, connection: sqlite3.Connection):
        for file in sorted(Directory.listdir(RESOURCES, '.*\.sql')):
            with open(file) as fd:
                script = fd.read()
                connection.executescript(script)
            connection.commit()

        insert_statement = 'INSERT OR IGNORE INTO `languages` VALUES (?, ?, ?)'
        for file in Directory.listdir(RESOURCES, '.*\.csv'):
            language_id = Path(path.basename(file)).stem.lower()
            with open(file) as fd:
                reader = csv.reader(fd, delimiter=',')
                connection.executemany(insert_statement, [(language_id, word, int(weight)) for word, weight in reader])
                connection.commit()
    
    def __split_words(self, text: str):
        return self.__cached_split_words(text.strip().lower()).copy()

    @lru_cache(maxsize=10)
    def __cached_split_words(self, text: str):
        return list(set(self.__pattern.findall(
            self.__sanitize_text(text)
        )))

    def __sanitize_text(self, text: str) -> str:
        return re.sub(r'[^\w\s]+|[\d]+', '', text)

    def __sanitize_by_language(self, text: str, expected_language) -> str:
        match expected_language:
            case 'ja' | 'zh' | 'zh-cn' | 'zh-tw':
                pattern = re.compile(r'[^\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]', re.IGNORECASE)
                return re.sub(pattern, '', text)
            case _:
                pattern = re.compile(r'[\u3040-\u30FF\u3400-\u4DBF\u4E00-\u9FFF]', re.IGNORECASE)
                return re.sub(pattern, '', text)

    def __try_detect(self, words: list[str]) -> list[LanguageDetectionResult]:
        results = []

        if words:
            connection = self.connection
            try:
                cursor = connection.cursor()
                parameters = ', '.join(['?'] * len(words))
                select_statement = \
                    f'SELECT `language_id`, COUNT(*), SUM(`weight`) AS "weight" FROM `languages` ' \
                    f'WHERE `word` IN ({parameters}) ' \
                    'GROUP BY `language_id` ' \
                    'ORDER BY "weight" DESC; '
                for language_id, count, score in cursor.execute(select_statement, tuple(words)).fetchall():
                    results.append(LanguageDetectionResult(language_id, count, score, len(words)))
            except sqlite3.Error as error:
                self.logger.error(error)
            finally:
                connection.close()
        
        return results

    def __try_detect_text(self, text: str) -> list[LanguageDetectionResult]:
        return self.__try_detect(self.__split_words(text))

    def __pre_training_validation(self, words: list[str], expected_language: str):
        if String.is_blank(expected_language):
            self.logger.warning('(Pre-training validation) Expected Language is blank!')
            return False

        if not words:
            self.logger.warning('(Pre-training validation) Input text is blank!')
            return False
        
        self.logger.info('(Pre-training validation) Verifying if training is necessary...')
        for result in self.__try_detect(words):
            if result.language_id != expected_language:
                continue
            self.logger.debug(f'(Pre-training validation) [word_count={len(words)}]  {result}')
            return result.count < len(words)
        self.logger.debug(f'(Pre-training validation) "{words}" does not match "{expected_language}"!')
        return True

    def __post_training_validation(self, words: list[str], expected_language: str):
        results = self.__try_detect(words)
        detected_languages = []
        for result in results:
            detected_languages.append(result.language_id)
            self.logger.debug(f'(Post-training validation) {result}')

        if expected_language in detected_languages:
            self.logger.info(f'(Post-training validation) Language of text detected: {detected_languages}')
        else:
            self.logger.warning(f'(Post-training validation) Language of text not detected: {detected_languages}')

    @property
    def connection(self):
        try:
            connection = sqlite3.connect(DATABASE_FILE, timeout=60)
            return connection
        except sqlite3.Error as error:
            self.logger.error(error)

    def detect(self, text: str) -> list[(str, float)]:
        highest_score = -1;
        detected_languages = []
        for result in self.__try_detect_text(text):
            self.logger.debug(f'Detection Result: {result}')
            if highest_score <= result.score and result.score:
                detected_languages.append((result.language_id, result.score))
                highest_score = result.score
        return detected_languages

    def train(self, text: str, expected_language: str):
        expected_language = expected_language.lower()
        words = self.__split_words(self.__sanitize_by_language(text, expected_language))
        if self.__pre_training_validation(words, expected_language):
            connection = self.connection
            try:
                insert_statement = 'INSERT OR IGNORE INTO `languages` VALUES (?, ?, ?)'
                connection.executemany(insert_statement, [(expected_language, word, 1) for word in words])
                connection.commit()
            except sqlite3.Error as error:
                self.logger.error(error)
            finally:
                connection.close()
                self.__post_training_validation(words, expected_language)


class LegacyDetectionModel(LanguageDetectionModel):
    def __init__(self):
        super().__init__()
        self.__lock = threading.Lock()

        self.__model = None
        self.__logger = get_logger('models')
    
    @property
    def logger(self):
        return self.__logger
    
    def __load_model(self):
        with self.__lock:
            self.logger.info(f'Loading all language models')
            self.__model = LanguageDetectorBuilder.from_all_languages().build()

    @property
    def model(self) -> LanguageDetector:
        if not self.__model:
            self.__load_model()
        return self.__model

    def detect(self, text: str) -> list[(str, float)]:
        detected_language = self.model.detect_language_of(text)
        return [(detected_language.iso_code_639_1.name.lower(), 1.0)]
    
    def train(self, text: str, expected_language: str):
        pass


class LazyLoadingDetectionModel(LanguageDetectionModel):
    def __init__(self, languages: list[str]):
        super().__init__()
        self.__lock = threading.Lock()
        self.__languages = set(languages.copy())

        self.__model = None
        self.__logger = get_logger('models')
    
    @property
    def logger(self):
        return self.__logger
    
    @cached_property
    def supported_languages(self):
        map = {}
        for language in Language.all():
            map[language.iso_code_639_1.name.lower()] = language
        return map
    
    def __get_language_enums(self, languages: Iterable[str]) -> list[Language]:
        enums = []
        for language in languages:
            if language in self.supported_languages.keys():
                enums.append(self.supported_languages[language])
        return enums

    def __load_model(self):
        with self.__lock:
            self.logger.info(f'Loading language models: [{", ".join(self.__languages)}]')
            self.__model = LanguageDetectorBuilder.from_languages(
                *self.__get_language_enums(self.__languages)
            ).build()

    @property
    def model(self) -> LanguageDetector:
        if not self.__model:
            self.__load_model()
        return self.__model

    def detect(self, text: str) -> list[(str, float)]:
        detected_language = self.model.detect_language_of(text)
        return [(detected_language.iso_code_639_1.name.lower(), 1.0)]
    
    def train(self, text: str, expected_language: str):
        expected_language = expected_language.lower()
        if expected_language in self.__languages:
            return
        self.__languages.add(expected_language)
        self.logger.info(f'Unloading language models')
        self.model.unload_language_models()
        self.__load_model()


class MorseCodeDetectionModel(LanguageDetectionModel):
    def __init__(self, model: LanguageDetectionModel):
        super().__init__()
        self.__model = model

    @property
    def model(self):
        return self.__model

    def detect(self, text: str):
        if re.match(r'[\.・\-\s]', text):
            return ('morse_code', 1.0)
        return self.model.detect(text)

    def train(self, text: str, expected_language: str):
        self.model.train(text, expected_language)
