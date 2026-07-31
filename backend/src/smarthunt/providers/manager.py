import logging
from typing import Dict, List, Optional, Any
from smarthunt.providers.base.provider import BaseProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manager class to handle registry and lifecycle of job providers."""

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}

    def register_provider(self, provider: BaseProvider) -> None:
        """Register a new job provider instance."""
        if not provider.name:
            raise ValueError("Provider name cannot be empty")
        self._providers[provider.name] = provider
        logger.info(f"Registered provider: {provider.name}")

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get provider by name."""
        return self._providers.get(name)

    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Get summary info for all registered providers."""
        return [
            {
                "name": p.name,
                "supports_login": getattr(p, "supports_login", False),
                "supports_apply": getattr(p, "supports_apply", False),
                "supports_resume_upload": getattr(p, "supports_resume_upload", False),
                "supports_cover_letter": getattr(p, "supports_cover_letter", False),
            }
            for p in self._providers.values()
        ]

    def get_statistics(self) -> Dict[str, int]:
        """Get capability statistics across registered providers."""
        providers = list(self._providers.values())
        return {
            "total": len(providers),
            "supports_login": sum(1 for p in providers if getattr(p, "supports_login", False)),
            "supports_apply": sum(1 for p in providers if getattr(p, "supports_apply", False)),
            "supports_resume_upload": sum(
                1 for p in providers if getattr(p, "supports_resume_upload", False)
            ),
            "supports_cover_letter": sum(
                1 for p in providers if getattr(p, "supports_cover_letter", False)
            ),
        }


provider_manager = ProviderManager()
