from smarthunt.providers.base.provider import BaseProvider


class ForasnagulfProvider(BaseProvider):
    name = "forasnagulf"

    async def search(self, query=None, location=None, page=1, limit=10):
        return [
            {
                "id": 11,
                "title": "Network Infrastructure Engineer",
                "provider": self.name,
                "location": "Muscat",
                "salary": 13000,
                "score": 81,
            }
        ]
