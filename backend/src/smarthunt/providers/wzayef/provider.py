from smarthunt.providers.base.provider import BaseProvider


class WzayefProvider(BaseProvider):
    name = "wzayef"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [
            {
                "id": 8,
                "title": "Linux Administrator",
                "provider": self.name,
                "location": "Jeddah",
                "salary": 11000,
                "score": 79,
            }
        ]
