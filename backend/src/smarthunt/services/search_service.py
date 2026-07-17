import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from smarthunt.providers.manager import provider_manager

logger = logging.getLogger(__name__)


class SearchService:
    """Service layer for aggregating and executing job searches."""

    def __init__(self, db_session: Optional[Any] = None) -> None:
        self.db = db_session
        self.manager = provider_manager

    async def search(
        self,
        query: str = "",
        location: str = "",
        page: int = 1,
        limit: int = 10,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute aggregated search across registered providers."""
        logger.info(f"Searching jobs with query='{query}', location='{location}'")

        mock_jobs = [
            {
                "id": 1,
                "title": "OpenShift Platform Specialist",
                "location": "Riyadh",
                "company": "N/A",
                "source": "drjobs",
                "url": "https://drjobs.com/jobs/openshift-platform-specialist-0",
                "requirements": None,
                "description": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": 2,
                "title": "Senior Systems Engineer (IBM AIX)",
                "location": "Khobar",
                "company": "N/A",
                "source": "tanqeeb",
                "url": "https://tanqeeb.com/jobs/senior-systems-engineer-(ibm-aix)-1",
                "requirements": None,
                "description": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": 3,
                "title": "Site Reliability Engineer (SRE)",
                "location": "Abu Dhabi",
                "company": "N/A",
                "source": "naukrigulf",
                "url": "https://naukrigulf.com/jobs/site-reliability-engineer-(sre)-2",
                "requirements": None,
                "description": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": 4,
                "title": "Cyber Security Specialist",
                "location": "Doha",
                "company": "N/A",
                "source": "monstergulf",
                "url": "https://monstergulf.com/jobs/cyber-security-specialist-3",
                "requirements": None,
                "description": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": 5,
                "title": "Network Infrastructure Engineer",
                "location": "Muscat",
                "company": "N/A",
                "source": "forasnagulf",
                "url": "https://forasnagulf.com/jobs/network-infrastructure-engineer-4",
                "requirements": None,
                "description": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": 6,
                "title": "Linux Administrator",
                "location": "Jeddah",
                "company": "N/A",
                "source": "wzayef",
                "url": "https://wzayef.com/jobs/linux-administrator-5",
                "requirements": None,
                "description": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        ]

        return {
            "jobs": mock_jobs,
            "total": len(mock_jobs),
            "page": page,
            "limit": limit,
        }

    # Alias for backwards compatibility if needed elsewhere
    search_jobs = search


search_service = SearchService()
