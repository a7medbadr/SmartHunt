from __future__ import annotations
from smarthunt.providers.linkedin.provider import LinkedInProvider
from smarthunt.providers.indeed.provider import IndeedProvider
from smarthunt.providers.gulftalent.provider import GulfTalentProvider
from smarthunt.providers.bayt.provider import BaytProvider
from smarthunt.providers.wuzzuf.provider import WuzzufProvider
from smarthunt.providers.naukrigulf.provider import NaukrigulfProvider
from smarthunt.providers.monstergulf.provider import MonstergulfProvider
from smarthunt.providers.wzayef.provider import WzayefProvider
from smarthunt.providers.tanqeeb.provider import TanqeebProvider
from smarthunt.providers.drjobs.provider import DrjobsProvider
from smarthunt.providers.forasnagulf.provider import ForasnagulfProvider

class ProviderRegistry:
    def providers(self):
        return [
            LinkedInProvider(),
            IndeedProvider(),
            GulfTalentProvider(),
            BaytProvider(),
            WuzzufProvider(),
            NaukrigulfProvider(),
            MonstergulfProvider(),
            WzayefProvider(),
            TanqeebProvider(),
            DrjobsProvider(),
            ForasnagulfProvider(),
        ]
