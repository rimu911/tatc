from tatc import core
from tatc.core.bots import TatcTwitchChatBot
from tatc.modules import load_modules


import signal


def main():
    bot = TatcTwitchChatBot(
        configuration=core.init(),
        modules=load_modules()
    )
    bot.run()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM,  signal.SIG_DFL)
    main()
