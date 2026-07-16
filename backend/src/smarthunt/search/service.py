from typing import Dict, Any

class SearchService:
    async def search_jobs(
        self, 
        title: str = None, 
        location: str = None, 
        provider: str = None, 
        page: int = 1, 
        limit: int = 10
    ) -> Dict[str, Any]:
        mock_jobs = [
            {"id": 1, "title": "Senior Linux System Administrator", "location": "Riyadh", "provider": "SmartHunt", "salary": 15000},
            {"id": 2, "title": "DevOps Engineer", "location": "Remote", "provider": "LinkedIn", "salary": 12000},
            {"id": 3, "title": "Infrastructure Engineer", "location": "Riyadh", "provider": "GulfTalent", "salary": 14000}
        ]
        
        filtered_jobs = mock_jobs
        if title:
            filtered_jobs = [j for j in filtered_jobs if title.lower() in j["title"].lower()]
        if location:
            filtered_jobs = [j for j in filtered_jobs if location.lower() in j["location"].lower()]
        if provider:
            filtered_jobs = [j for j in filtered_jobs if provider.lower() in j["provider"].lower()]
            
        return {
            "items": filtered_jobs,
            "count": len(filtered_jobs),
            "page": page
        }

search_service = SearchService()
