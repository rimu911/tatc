from __future__ import annotations

import re
import emoji


class TwitchEmote:
    def __init__(self, emote_id: str, data: str):
        start_index, end_index = data.strip().split('-')
        self.__emote_id = emote_id
        self.__start_index = int(start_index.strip())
        self.__end_index = int(end_index.strip()) + 1
    
    def __hash__(self) -> int:
        return hash(self.__emote_id)

    def __eq__(self, other: any):
        return isinstance(other, TwitchEmote) and (
            other.start_index == self.start_index and other.end_index == self.end_index
        )

    @property
    def end_index(self) -> int:
        return self.__end_index

    @property
    def start_index(self) -> int:
        return self.__start_index

    @staticmethod
    def parse(tags: str, include_duplicates: bool = False) -> list[TwitchEmote]:
        emotes = []
        if not tags:
            return emotes
        
        for tag in tags.split('/'):
            if not tag:
                continue
            emote_id, index_ranges = tag.split(':')
            # when multiple same emotes are used, comma delimited values are provided
            for index_range in index_ranges.split(','):
                emotes.append(TwitchEmote(emote_id, index_range))

        if not include_duplicates:
            emotes = list(set(emotes))

        return sorted(emotes, key=lambda emote: emote.start_index)


class Twitch:
    @staticmethod
    def sanitize_twitch_emotes(message: str, emotes: list[TwitchEmote] = None):
        if not emotes:
            return message.strip()

        emotes_terms = []
        for emote in set(emotes):
            emotes_terms.append(message[emote.start_index:emote.end_index])

        for term in emotes_terms:
            message = message.replace(term, '')

        return message.strip()

    @staticmethod
    def sanitize_emojis(message: str):
        return emoji.replace_emoji(message, '').strip()

    @staticmethod
    def sanitize_username(message: str):
        # important: twitch username can contain non-latin characters
        return re.sub(r'@[\S]{4,25}', '', message, re.IGNORECASE).strip()

    @staticmethod
    def sanitize_uris(message: str):
        return re.sub(r'[a-z]+://[\S]+', '', message, re.IGNORECASE)
