import signal

import fast_langdetect

import config
from app import TwitchChatBot

__app_name__ = 'TaTC is another Translation Chatbot'


def main():
    init()
    bot = TwitchChatBot()
    bot.run()


def init():
    """
    Initialize fast_langdetect memory models
    """
    fast_langdetect.detect_langs("Hello World", low_memory=config.low_memory_mode())


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM,  signal.SIG_DFL)
    main()
