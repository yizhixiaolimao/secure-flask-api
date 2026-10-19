"""HTTP hardening header tests."""


def test_security_headers_are_present(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]


def test_oversized_request_is_rejected(client):
    response = client.post(
        "/auth/login",
        data=b"x" * 20_000,
        content_type="application/json",
    )

    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == "payload_too_large"

