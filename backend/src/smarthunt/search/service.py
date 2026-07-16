from typing import Dict, Any
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

        # فلترة بسيطة مبدئية بناءً على العنوان لو مبعوث
        filtered_jobs = mock_jobs
        if title:
            filtered_jobs = [j for j in mock_jobs if title.lower() in j["title"].lower()]

        # حسابات الـ Pagination اليدوية لتفادي الموديول الناقص
        total_items = len(filtered_jobs)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_items = filtered_jobs[start_idx:end_idx]

        # إرجاع نفس شكل الـ Response المتوقع من الـ API
        return {
            "items": paginated_items,
            "total": total_items,
            "page": page,
            "limit": limit,
            "pages": (total_items + limit - 1) // limit
        }

search_service = SearchService()
