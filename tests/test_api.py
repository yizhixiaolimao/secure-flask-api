"""Protected endpoint and output-encoding tests."""


def test_protected_data_rejects_missing_token(client):
    response = client.get("/api/data")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authorization_required"


def test_protected_data_accepts_valid_token(client, auth_headers):
    response = client.get("/api/data", headers=auth_headers)

    assert response.status_code == 200
    assert response.get_json() == {"count": 0, "data": []}


def test_create_post_and_escape_xss_payload(client, auth_headers):
    response = client.post(
        "/api/posts",
        headers=auth_headers,
        json={
            "title": "<script>alert('xss')</script>",
            "content": '<img src=x onerror="alert(1)">',
            "author_id": 999,
        },
    )

    assert response.status_code == 201
    post = response.get_json()["data"]
    assert post["author"] == "alice"
    assert "<script>" not in post["title"]
    assert "&lt;script&gt;" in post["title"]
    assert "<img" not in post["content"]
    assert "&lt;img" in post["content"]

    list_response = client.get("/api/data", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.get_json()["data"][0] == post


def test_post_validation_rejects_empty_fields(client, auth_headers):
    response = client.post(
        "/api/posts",
        headers=auth_headers,
        json={"title": "", "content": "hello"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "validation_error"


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/data", headers={"Authorization": "Bearer definitely-not-a-jwt"}
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_token"

