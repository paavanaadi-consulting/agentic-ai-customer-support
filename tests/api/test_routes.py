import pytest
from fastapi.testclient import TestClient
from src.api.routes import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
