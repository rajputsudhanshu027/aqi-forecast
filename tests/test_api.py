from fastapi.testclient import TestClient

from aqi.serve.app import app


def test_invalid_request_returns_422():
    with TestClient(app) as client:
        response = client.post(
            "/predict",
            json={
                "city": "Delhi",
                "pm25": -500,
            },
        )

    assert response.status_code == 422


@app.get("/metrics")
def metrics():
    return {"message": "Metrics instrumentation comes in Phase 8."}
