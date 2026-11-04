from backend.services.ontology_service import OntologyService
def test_real_counts():
    s=OntologyService(); stats=s.stats()
    assert stats=={"triples":1228,"classes":45,"object_properties":22,"datatype_properties":24,"individuals":80}
def test_defined_profile_classes():
    ids={x["id"] for x in OntologyService().classes()}
    assert {"ProfilSOPK","ProfilEndometriose","ProfilAlerteOestrogene"}<=ids
def test_api(client):
    r=client.get("/api/ontology/stats");assert r.status_code==200 and r.json()["triples"]==1228
    assert client.get("/api/ontology/class/ProfilSOPK").status_code==200
    assert client.get("/api/ontology/class/DoesNotExist").status_code==404
