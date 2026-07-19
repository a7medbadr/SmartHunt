from datetime import datetime, timezone
from typing import List
from smarthunt.saved_searches.schemas import SavedSearchCreate


class SavedSearchService:
    def __init__(self):
        self._searches: List[dict] = []
        self._counter = 1

    def create(self, data: SavedSearchCreate) -> dict:
        item = {
            "id": self._counter,
            "name": data.name,
            "keyword": data.keyword,
            "location": data.location,
            "source": data.source,
            "created_at": datetime.now(timezone.utc),
        }
        self._counter += 1
        self._searches.append(item)
        return item

    def list_all(self) -> List[dict]:
        return self._searches

    def delete(self, search_id: int) -> bool:
        for i, item in enumerate(self._searches):
            if item["id"] == search_id:
                self._searches.pop(i)
                return True
        return False

    def clear(self):
        self._searches.clear()
        self._counter = 1


saved_search_service = SavedSearchService()
