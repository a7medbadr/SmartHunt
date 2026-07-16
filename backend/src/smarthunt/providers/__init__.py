from smarthunt.providers.registry.registry import ProviderRegistry
from smarthunt.providers.linkedin.provider import LinkedInProvider
from smarthunt.providers.indeed.provider import IndeedProvider
from smarthunt.providers.bayt.provider import BaytProvider
from smarthunt.providers.gulftalent.provider import GulfTalentProvider
from smarthunt.providers.wuzzuf.provider import WuzzufProvider

registry = ProviderRegistry()
registry.register(LinkedInProvider())
registry.register(IndeedProvider())
registry.register(BaytProvider())
registry.register(GulfTalentProvider())
registry.register(WuzzufProvider())
