
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_prime_task():
    payload = {"task": "Write a Python function to check if a number is prime"}

    r = requests.post(BASE_URL + "/run", json=payload)
    data = r.json()

    assert "result" in data
    assert isinstance(data["result"], str)
    assert len(data["result"]) > 20
