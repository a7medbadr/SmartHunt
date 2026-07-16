from smarthunt.providers.base.provider import BaseProvider

class BaytProvider(BaseProvider):
    name = "bayt"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [{
            "id": 4,
            "title": "Cloud Solutions Architect",
            "provider": self.name,
            "location": "Dubai",
            "salary": 18000,
            "score": 95,
        }]
