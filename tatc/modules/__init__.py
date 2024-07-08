# register the modules to be loaded here
from tatc import core
from tatc.modules.translations import TatcTranslationChannelModule

_configuration_ = core.init()
_registered_modules_ = [
    TatcTranslationChannelModule(_configuration_)
]


def load_modules():
    return _registered_modules_.copy()
