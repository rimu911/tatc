class UnauthorizedUserError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class UnknownModuleError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class InvalidArgumentsError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class ModuleNotEnabledError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)
