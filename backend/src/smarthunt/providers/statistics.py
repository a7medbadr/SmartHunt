from __future__ import annotations

from smarthunt.providers.registry import ProviderRegistry


class ProviderStatistics:
    def __init__(self):
        self.registry = ProviderRegistry()

    def get_summary(self) -> dict[str, int]:
        providers = self.registry.providers()
        total = len(providers)

        supports_login = 0
        supports_apply = 0
        supports_resume_upload = 0
        supports_cover_letter = 0

        for provider in providers:
            if getattr(provider, "supports_login", False):
                supports_login += 1
            if getattr(provider, "supports_apply", False):
                supports_apply += 1
            if getattr(provider, "supports_resume_upload", False):
                supports_resume_upload += 1
            if getattr(provider, "supports_cover_letter", False):
                supports_cover_letter += 1

        return {
            "total": total,
            "supports_login": supports_login,
            "supports_apply": supports_apply,
            "supports_resume_upload": supports_resume_upload,
            "supports_cover_letter": supports_cover_letter,
        }


provider_stats = ProviderStatistics()
