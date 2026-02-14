import json
import os
from os import environ, path
from dotenv import load_dotenv
from os import path

load_dotenv(path.join(
    os.getcwd(),
    '.env'
))


def root_directory() -> str:
    return os.getcwd()


def load_channels_configurations() -> dict:
    file = path.join(f'{root_directory()}', 'channels.json')
    if path.exists(file):
        print(f'Loading configurations from "{file}"')
        with open(file, 'r') as fp:
            return dict(json.load(fp))
    return {}


def save_channels_configurations(data: dict):
    file = path.join(f'{root_directory()}', 'channels.json')
    print(f'Saving configurations to "{file}"')
    with open(file, 'w') as fp:
        json.dump(data, fp, indent=2)


def twitch_access_token() -> str:
    return environ.get('twitch_access_token')


def bot_administrators() -> list[str]:
    administrators = [
        administrator.strip() for administrator in environ.get('bot_administrators', '').split(',')
    ]
    return administrators


def default_translation_engine() -> str:
    return environ.get('default_translation_engine', 'google')


def default_ignore_words() -> set[str]:
    return set(environ.get('default_ignore_words', '').split(','))
