from smarthunt.providers.circuit_breaker import (
    CircuitBreaker,
)

_provider_circuits: dict[
    str,
    CircuitBreaker,
] = {}


def get_circuit(
    provider: str,
) -> CircuitBreaker:

    provider = provider.lower()

    if provider not in _provider_circuits:
        _provider_circuits[provider] = CircuitBreaker()

    return _provider_circuits[provider]


def clear_circuits() -> None:
    _provider_circuits.clear()
