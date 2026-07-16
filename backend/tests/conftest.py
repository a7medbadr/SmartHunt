import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager

# إضافة المسار الصحيح للـ backend/src
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

from smarthunt.main import app  # noqa: E402


@pytest.fixture
async def client():
    # LifespanManager بيبعت startup/shutdown events للـ app
    # (لازم لو عندك DB connection أو أي حاجة بتتظبط في startup)
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
