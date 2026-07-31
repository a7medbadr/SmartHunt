from fastapi import FastAPI
from fastapi.testclient import TestClient

from smarthunt.middleware.request_logging import RequestLoggingMiddleware


def test_request_logging_middleware():
    app = FastAPI()

    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {
            "status": "ok",
        }

    client = TestClient(app)

    response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
