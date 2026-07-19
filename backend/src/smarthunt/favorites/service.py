from datetime import datetime, timezone
from typing import List
from smarthunt.favorites.schemas import FavoriteJobCreate


class FavoriteAlreadyExistsError(Exception):
    pass


class FavoritesService:
    def __init__(self):
        self._favorites: List[dict] = []
        self._counter = 1

    def add_favorite(self, data: FavoriteJobCreate) -> dict:
        str_job_id = str(data.job_id)
        for fav in self._favorites:
            if str(fav["job_id"]) == str_job_id:
                raise FavoriteAlreadyExistsError(f"Job with id {str_job_id} is already in favorites")

        item = {
            "id": self._counter,
            "job_id": str_job_id,
            "title": data.title,
            "company": data.company or "N/A",
            "source": data.source or "N/A",
            "created_at": datetime.now(timezone.utc),
        }
        self._counter += 1
        self._favorites.append(item)
        return item

    def list_favorites(self) -> List[dict]:
        return self._favorites

    def delete_favorite(self, fav_id: str) -> bool:
        str_id = str(fav_id)
        for i, item in enumerate(self._favorites):
            if str(item["id"]) == str_id or str(item["job_id"]) == str_id:
                self._favorites.pop(i)
                return True
        return False

    def clear(self):
        self._favorites.clear()
        self._counter = 1


favorites_service = FavoritesService()
