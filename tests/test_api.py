
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    r = requests.get(BASE_URL + "/docs")
    assert r.status_code == 200

def test_run_endpoint():
    payload = {"task": "Say hello"}

    r = requests.post(
        BASE_URL + "/run",
        json=payload
    )

    assert r.status_code == 200
    assert "result" in r.json()
