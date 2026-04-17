
import requests

BASE_URL = "http://127.0.0.1:8000"

TASK = "Write a function that reverses a string"

def get_response():
    return requests.post(
        BASE_URL + "/run",
        json={"task": TASK}
    ).json()["result"]

def test_consistency():
    r1 = get_response()
    r2 = get_response()

    overlap = len(set(r1.split()) & set(r2.split()))
    assert overlap > 5
