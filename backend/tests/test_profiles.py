from backend.models.profil import ProfilCreate
from backend import crud
from backend.tests.conftest import FakeSparql
def test_profile_validation():
    p=ProfilCreate(identifiant="TEST-1",age=25,imc=22,fume=False,conditions=[]);assert p.age==25
def test_list_builds_controlled_query():
    f=FakeSparql([]);crud.list_profiles(f,20,35,False,"SOPK");q=f.queries[0]
    assert "?age >= 20" in q and "ptc:SOPK" in q and "DROP" not in q
def test_api_validation(client):assert client.post("/api/profils",json={"identifiant":"x","age":2,"imc":2}).status_code==422
def test_list_api(client):assert client.get("/api/profils").status_code==200
