from smarthunt.providers.base.provider import BaseProvider


class NaukrigulfProvider(BaseProvider):
    name = "naukrigulf"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [
            {
                "id": 6,
                "title": "Site Reliability Engineer (SRE)",
                "provider": self.name,
                "location": "Abu Dhabi",
                "salary": 16000,
                "score": 89,
            }
        ]
