from smarthunt.providers.base.provider import BaseProvider


class TanqeebProvider(BaseProvider):
    name = "tanqeeb"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [
            {
                "id": 9,
                "title": "Senior Systems Engineer (IBM AIX)",
                "provider": self.name,
                "location": "Khobar",
                "salary": 16500,
                "score": 93,
            }
        ]
