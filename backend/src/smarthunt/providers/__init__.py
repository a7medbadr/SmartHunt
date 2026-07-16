from smarthunt.providers.registry.registry import ProviderRegistry
from smarthunt.providers.linkedin import provider as linkedin

registry = ProviderRegistry()
registry.register(linkedin)
