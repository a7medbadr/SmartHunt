from typing import Dict, Any
from smarthunt.shared.pagination import create_paginated_response
from smarthunt.search.filters import JobFilters

class SearchService:
    async def search_jobs(
        self, 
        title: str = None, 
        location: str = None, 
        provider: str = None, 
        page: int = 1, 
        limit: int = 10,
        filters: JobFilters = None
    ) -> Dict[str, Any]:
        mock_jobs = [
            {"id": 1, "title": "Senior Linux System Administrator", "location": "Riyadh", "provider": "SmartHunt", "salary": 15000, "experience": "senior", "remote": False, "onsite": True, "hybrid": False, "country": "Saudi Arabia", "city": "Riyadh"},
            {"id": 2, "title": "DevOps Engineer", "location": "Remote", "provider": "LinkedIn", "salary": 12000, "experience": "mid", "remote": True, "onsite": False, "hybrid": False, "country": "US", "city": "Remote"},
            {"id": 3, "title": "Infrastructure Engineer", "location": "Riyadh", "provider": "GulfTalent", "salary": 14000, "experience": "senior", "remote": False, "onsite": False, "hybrid": True, "country": "Saudi Arabia", "city": "Riyadh"}
        ]
        
        filtered_jobs = mock_jobs
        if title:
            filtered_jobs = [j for j in filtered_jobs if title.lower() in j["title"].lower()]
        if location:
            filtered_jobs = [j for j in filtered_jobs if location.lower() in j["location"].lower()]
        if provider:
            filtered_jobs = [j for j in filtered_jobs if provider.lower() in j["provider"].lower()]
            
        if filters:
            if filters.experience:
                filtered_jobs = [j for j in filtered_jobs if j.get("experience") == filters.experience]
            if filters.remote is not None:
                filtered_jobs = [j for j in filtered_jobs if j.get("remote") == filters.remote]
            if filters.onsite is not None:
                filtered_jobs = [j for j in filtered_jobs if j.get("onsite") == filters.onsite]
            if filters.hybrid is not None:
                filtered_jobs = [j for j in filtered_jobs if j.get("hybrid") == filters.hybrid]
            if filters.salary_min is not None:
                filtered_jobs = [j for j in filtered_jobs if j.get("salary", 0) >= filters.salary_min]
            if filters.salary_max is not None:
                filtered_jobs = [j for j in filtered_jobs if j.get("salary", 0) <= filters.salary_max]
            if filters.country:
                filtered_jobs = [j for j in filtered_jobs if j.get("country", "").lower() == filters.country.lower()]
            if filters.city:
                filtered_jobs = [j for j in filtered_jobs if j.get("city", "").lower() == filters.city.lower()]
                
        return create_paginated_response(filtered_jobs, len(filtered_jobs), page, limit)

search_service = SearchService()
