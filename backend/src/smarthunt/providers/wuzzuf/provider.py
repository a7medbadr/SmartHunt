from smarthunt.providers.base.provider import BaseProvider

class WuzzufProvider(BaseProvider):
    name = "wuzzuf"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [{
            "id": 5,
            "title": "Python Backend Developer (FastAPI)",
            "provider": self.name,
            "location": "Cairo",
            "salary": 45000,
            "score": 82,
        }]
