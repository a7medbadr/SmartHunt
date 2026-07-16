from smarthunt.providers.base.provider import BaseProvider

class IndeedProvider(BaseProvider):
    name = "indeed"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [{
            "id": 2,
            "title": "DevOps Engineer",
            "provider": self.name,
            "location": "Remote",
            "salary": 12000,
            "score": 88,
        }]
