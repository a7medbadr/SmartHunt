import pytest
from smarthunt.saved_searches.schemas import SavedSearchCreate
from smarthunt.saved_searches.service import saved_search_service


@pytest.fixture(autouse=True)
def reset_service():
    saved_search_service.clear()


def test_create_saved_search():
    data = SavedSearchCreate(
        name="Linux in Riyadh",
        keyword="linux",
        location="riyadh",
        source="linkedin",
    )
    res = saved_search_service.create(data)
    assert res["id"] == 1
    assert res["name"] == "Linux in Riyadh"
    assert res["keyword"] == "linux"
    assert res["location"] == "riyadh"
    assert res["source"] == "linkedin"


def test_list_saved_searches():
    data1 = SavedSearchCreate(name="Search 1", keyword="python")
    data2 = SavedSearchCreate(name="Search 2", keyword="devops")
    saved_search_service.create(data1)
    saved_search_service.create(data2)

    items = saved_search_service.list_all()
    assert len(items) == 2
    assert items[0]["name"] == "Search 1"
    assert items[1]["name"] == "Search 2"


def test_delete_saved_search():
    data = SavedSearchCreate(name="To Delete", keyword="docker")
    created = saved_search_service.create(data)
    search_id = created["id"]

    # Delete existing
    deleted = saved_search_service.delete(search_id)
    assert deleted is True
    assert len(saved_search_service.list_all()) == 0

    # Delete non-existing
    deleted_again = saved_search_service.delete(999)
    assert deleted_again is False


def test_invalid_request():
    with pytest.raises(Exception):
        SavedSearchCreate()
