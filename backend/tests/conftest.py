import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

# إضافة المسار الصحيح للـ backend/src
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

from smarthunt.main import app  # noqa: E402


@pytest.fixture
async def client():
    # تشغيل الـ lifespan الخاص بالتطبيق يدوياً لضمان بناء وإغلاق قاعدة البيانات
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
