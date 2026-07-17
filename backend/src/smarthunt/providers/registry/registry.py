from __future__ import annotations

from typing import List

from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.bayt.provider import BaytProvider
from smarthunt.providers.drjobs.provider import DrjobsProvider
from smarthunt.providers.forasnagulf.provider import ForasnagulfProvider
from smarthunt.providers.gulftalent.provider import GulfTalentProvider
from smarthunt.providers.indeed.provider import IndeedProvider
from smarthunt.providers.linkedin.provider import LinkedInProvider
from smarthunt.providers.monstergulf.provider import MonstergulfProvider
from smarthunt.providers.naukrigulf.provider import NaukrigulfProvider
from smarthunt.providers.tanqeeb.provider import TanqeebProvider
from smarthunt.providers.wuzzuf.provider import WuzzufProvider
from smarthunt.providers.wzayef.provider import WzayefProvider


class ProviderRegistry:
    def providers(self) -> List[BaseProvider]:
        """Returns a list of all registered job search providers."""
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
