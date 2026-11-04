def test_root(client): assert client.get("/").status_code==200
def test_openapi(client): assert client.get("/openapi.json").status_code==200
def test_health(client): assert client.get("/api/health").json()["status"]=="healthy"
