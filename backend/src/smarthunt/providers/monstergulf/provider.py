from smarthunt.providers.base.provider import BaseProvider


class MonstergulfProvider(BaseProvider):
    name = "monstergulf"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [
            {
                "id": 7,
                "title": "Cyber Security Specialist",
                "provider": self.name,
                "location": "Doha",
                "salary": 15500,
                "score": 87,
            }
        ]
