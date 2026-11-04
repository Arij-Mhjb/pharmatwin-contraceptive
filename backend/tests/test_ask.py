from backend.routes import ask
def test_ask_contract(client,monkeypatch):
    monkeypatch.setattr(ask,"translate",lambda q:{"intent":"list_profiles","entities":[],"sparql":"SELECT * WHERE {}"})
    r=client.post("/api/ask",json={"question":"Liste les profils"});assert r.status_code==200
    assert set(r.json())=={"intent","entities","sparql","results"}
def test_ask_length(client):assert client.post("/api/ask",json={"question":"x"}).status_code==422
