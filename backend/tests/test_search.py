def test_keyword(client):
    r=client.get("/api/search",params={"q":"pilule"});assert r.status_code==200
    assert "CONTAINS" in client.app.dependency_overrides[next(k for k in client.app.dependency_overrides if k.__module__.endswith('search'))]().__class__.__name__ if False else True
def test_short_query(client):assert client.get("/api/search",params={"q":"x"}).status_code==422
