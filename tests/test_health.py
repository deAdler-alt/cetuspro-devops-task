from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)


def test_health_ok_when_redis_available():
    with patch("app.main.get_redis") as mock_redis:
        mock_redis.return_value.ping.return_value = True
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "connected"}


def test_health_degraded_when_redis_down():
    import redis as redis_lib

    with patch("app.main.get_redis") as mock_redis:
        mock_redis.return_value.ping.side_effect = redis_lib.exceptions.ConnectionError()
        response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "redis": "unreachable"}


def test_home_returns_html():
    with patch("app.main.get_redis") as mock_redis:
        mock_redis.return_value.incr.return_value = 42
        response = client.get("/")
    assert response.status_code == 200
    assert "CetusPro" in response.text
