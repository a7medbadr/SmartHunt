import pytest
from smarthunt.favorites.schemas import FavoriteJobCreate
from smarthunt.favorites.service import favorites_service, FavoriteAlreadyExistsError


@pytest.fixture(autouse=True)
def reset_service():
    favorites_service.clear()


def test_add_favorite():
    data = FavoriteJobCreate(
        job_id="101",
        title="Senior Linux Engineer",
        company="RedHat",
        source="LinkedIn",
    )
    res = favorites_service.add_favorite(data)
    assert res["id"] == 1
    assert res["job_id"] == "101"
    assert res["title"] == "Senior Linux Engineer"


def test_list_favorites():
    fav1 = FavoriteJobCreate(job_id=1, title="Job 1")
    fav2 = FavoriteJobCreate(job_id=2, title="Job 2")
    favorites_service.add_favorite(fav1)
    favorites_service.add_favorite(fav2)

    items = favorites_service.list_favorites()
    assert len(items) == 2
    assert items[0]["title"] == "Job 1"
    assert items[1]["title"] == "Job 2"


def test_delete_favorite():
    fav = FavoriteJobCreate(job_id="202", title="DevOps Role")
    created = favorites_service.add_favorite(fav)

    success = favorites_service.delete_favorite(created["id"])
    assert success is True
    assert len(favorites_service.list_favorites()) == 0


def test_duplicate_favorite():
    fav1 = FavoriteJobCreate(job_id="303", title="FastAPI Engineer")
    favorites_service.add_favorite(fav1)

    fav_duplicate = FavoriteJobCreate(job_id="303", title="FastAPI Engineer Duplicate")
    with pytest.raises(FavoriteAlreadyExistsError):
        favorites_service.add_favorite(fav_duplicate)


def test_invalid_request():
    with pytest.raises(Exception):
        FavoriteJobCreate(job_id="404")
