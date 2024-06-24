class UnauthorizedUserError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)


class InvalidArgumentsError(Exception):
    def __init__(self, message: str = None):
        super().__init__(message)
