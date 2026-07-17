from collections import deque

_HISTORY = deque(maxlen=100)


def save(query: str, provider: str, results: int):
    _HISTORY.append(
        {
            "query": query,
            "provider": provider,
            "results": results,
        }
    )


def all():
    return list(_HISTORY)
