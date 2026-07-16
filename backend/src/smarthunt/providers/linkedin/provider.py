from smarthunt.providers.base.provider import BaseProvider

class LinkedInProvider(BaseProvider):
    name = "linkedin"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [{
            "id": 1,
            "title": "Senior Linux System Administrator",
            "provider": self.name,
            "location": "Riyadh",
            "salary": 15000,
            "score": 91,
        }]
