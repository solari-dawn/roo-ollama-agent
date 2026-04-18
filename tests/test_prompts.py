import os
import requests

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-API-Key": os.getenv("API_KEY", "dev-key")}
TASK = "Write a function that reverses a string"


def get_response() -> str:
    r = requests.post(BASE_URL + "/run", json={"task": TASK}, headers=HEADERS)
    r.raise_for_status()
    return r.json()["result"]


def test_consistency():
    r1 = get_response()
    r2 = get_response()

    overlap = len(set(r1.split()) & set(r2.split()))
    assert overlap > 5
