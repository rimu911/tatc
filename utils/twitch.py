from __future__ import annotations
from emoji import replace_emoji

import re


def parse_twitch_emotes(tags: str) -> list[TwitchEmote]:
    emotes = []
    if not tags:
        return emotes

    for tag in tags.split('/'):
        if not tag:
            continue
        # when multiple same emotes are used, comma delimited values are provided
        emote_id, index_ranges = tag.split(':')
        for index_range in index_ranges.split(','):
            emotes.append(TwitchEmote(emote_id, index_range))

    return sorted(emotes, key=lambda emote: emote.start_index)


def sanitize_twitch_message(
    message: str,
    emotes: list[TwitchEmote] = None,
    remove_emojis: bool = False,
    remove_usernames: bool = False,
    method: str = 'simple'
):
    if emotes:
        new_message = ''
        match method:
            case 'safe':
                for i in range(len(emotes)):
                    if i == 0:
                        sliced_message = message[:emotes[i].start_index]
                    else:
                        sliced_message = message[emotes[i-1].end_index:emotes[i].start_index]
                        if i == len(emotes)-1:
                            sliced_message += message[emotes[i].end_index:]
                    new_message += sliced_message
            case 'simple':
                emotes_terms = []
                for emote in set(emotes):
                    emotes_terms.append(message[emote.start_index:emote.end_index])

                new_message = message
                for emote_term in set(emotes_terms):
                    new_message = new_message.replace(emote_term, '')

        message = new_message

    if remove_usernames:
        message = re.sub(r'@[a-z0-9_]{4,25}', '', message, re.IGNORECASE).strip()

    if remove_emojis:
        message = replace_emoji(message, '').strip()

    return message.strip()


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