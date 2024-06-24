import config
import copy


class ChannelConfiguration:
    def __init__(
        self,
        data: dict[str, any] = None
    ):
        self.__config = {} if data is None else data

    @property
    def enabled(self) -> bool:
        return self.__config.setdefault('enabled', True)

    @property
    def translation_engine(self) -> str:
        return self.__config.setdefault('translation_engine', None) or config.default_translation_engine()

    @property
    def target_languages(self) -> list[str]:
        return self.__config.setdefault('target_languages', [])

    @property
    def ignore_languages(self) -> list[str]:
        return self.__config.setdefault('ignore_languages', [])

    @property
    def debug_mode(self) -> bool:
        return self.__config.setdefault('debug_mode', False) or False

    @property
    def remove_emojis(self) -> bool:
        return self.__config.setdefault('remove_emojis', True) or False

    @property
    def ignore_words(self) -> set:
        return self.__config.setdefault('ignore_words', config.default_ignore_words())

    @property
    def remove_usernames(self) -> bool:
        return self.__config.setdefault('remove_usernames', False) or False

    @enabled.setter
    def enabled(self, value: bool):
        self.__config['enabled'] = value

    @translation_engine.setter
    def translation_engine(self, value: str):
        self.__config['translation_engine'] = value or config.default_translation_engine()

    @target_languages.setter
    def target_languages(self, value: list[str]):
        self.__config['target_languages'] = [v.strip() for v in value]

    @ignore_languages.setter
    def ignore_languages(self, value: list[str]):
        self.__config['ignore_languages'] = [v.strip() for v in value]

    @ignore_words.setter
    def ignore_words(self, value: set[str]):
        self.__config['ignore_words'] = list(set([v.strip() for v in value]))

    @debug_mode.setter
    def debug_mode(self, value: bool):
        self.__config['debug_mode'] = value

    @remove_emojis.setter
    def remove_emojis(self, value: bool):
        self.__config['remove_emojis'] = value

    @remove_usernames.setter
    def remove_usernames(self, value: bool):
        self.__config['remove_usernames'] = value

    def to_dict(self) -> dict:
        return copy.deepcopy(self.__config)
