from smarthunt.providers.base.provider import BaseProvider

class DrjobsProvider(BaseProvider):
    name = "drjobs"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [{
            "id": 10,
            "title": "OpenShift Platform Specialist",
            "provider": self.name,
            "location": "Riyadh",
            "salary": 17500,
            "score": 94,
        }]
