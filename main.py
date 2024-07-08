import signal

import fast_langdetect

import config
from tatc import core
from tatc.core.bots import TatcTwitchChatBot
from tatc.modules import load_modules


def main():
    init_language_detection()
    bot = TatcTwitchChatBot(
        configuration=core.init(),
        modules=load_modules()
    )
    bot.run()


def init_language_detection():
    """
    Initialize fast_langdetect memory models
    """
    fast_langdetect.detect_langs("Hello World", low_memory=config.low_memory_mode())


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM,  signal.SIG_DFL)
    main()
