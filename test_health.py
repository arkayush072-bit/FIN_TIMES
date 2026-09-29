def test_health_returns_200_with_expected_shape(client):
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FinNews AI"
    assert isinstance(data["news_api_configured"], bool)
    assert isinstance(data["groq_api_configured"], bool)
    assert isinstance(data["demo_mode"], bool)


def test_health_never_exposes_key_values(client):
    resp = client.get("/health")
    body_text = resp.text.lower()
    # The response should only ever contain booleans about configuration,
    # never anything that looks like an actual key.
    assert "news_api_key" not in body_text
    assert "groq_api_key" not in body_text
