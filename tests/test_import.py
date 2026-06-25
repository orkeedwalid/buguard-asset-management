import pytest
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_bulk_import():
    response = client.post("/import", json={
        "assets": [
            {
                "id": "t1",
                "type": "domain",
                "value": "test.com",
                "status": "active",
                "source": "scan",
                "tags": ["test"],
                "metadata": {}
            }
        ]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert data["failed"] == 0

def test_deduplication():
    payload = {
        "assets": [
            {
                "id": "t2",
                "type": "domain",
                "value": "dedup-test.com",
                "status": "active",
                "source": "scan",
                "tags": ["original"],
                "metadata": {}
            }
        ]
    }
    client.post("/import", json=payload)
    response = client.post("/import", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 1
    assert data["imported"] == 0

def test_list_assets():
    response = client.get("/assets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_filter_by_type():
    response = client.get("/assets?type=domain")
    assert response.status_code == 200
    for asset in response.json():
        assert asset["type"] == "domain"

def test_malformed_record():
    response = client.post("/import", json={
        "assets": [
            {
                "type": "",
                "value": "",
                "status": "active",
                "source": "scan",
                "tags": [],
                "metadata": {}
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["failed"] == 1

def test_asset_not_found():
    response = client.get("/assets/nonexistent-id")
    assert response.status_code == 404