import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.routes import health, profils, search, ask, contraceptifs

class FakeSparql:
    def __init__(self, rows=None): self.rows=rows or []; self.queries=[]; self.updates=[]
    def run_select(self,q,**kwargs): self.queries.append(q); return self.rows
    def run_update(self,q): self.updates.append(q)

@pytest.fixture
def fake(): return FakeSparql([{"ok":1}])
@pytest.fixture
def client(fake):
    for router in (health,profiles if False else profils,search,ask,contraceptifs):
        app.dependency_overrides[router.client]=lambda:fake
    yield TestClient(app)
    app.dependency_overrides.clear()
