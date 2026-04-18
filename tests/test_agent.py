import os
import requests

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-API-Key": os.getenv("API_KEY", "dev-key")}


def test_prime_task():
    r = requests.post(
        BASE_URL + "/run",
        json={"task": "Write a Python function to check if a number is prime"},
        headers=HEADERS,
    )
    data = r.json()

    assert r.status_code == 200
    assert "result" in data
    assert isinstance(data["result"], str)
    assert len(data["result"]) > 20
