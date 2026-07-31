class AIError(Exception):
    pass


class AIProviderError(AIError):
    pass


class AITimeoutError(AIError):
    pass


class AIRetryExceededError(AIError):
    pass
