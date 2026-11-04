"""Non-destructive live API smoke check; the backend and Fuseki must be running.

Run: python -m backend.scripts.check_live
The default check is read-only; --crud manages only its own disposable profile.
"""
import httpx
import argparse
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crud", action="store_true", help="Create, edit and remove only a uniquely named disposable test profile")
    args = parser.parse_args()
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=60) as client:
        for path in ("/api/health", "/api/ontology/conditions", "/api/profils", "/api/search?q=pilule"):
            response = client.get(path)
            response.raise_for_status()
            print(f"OK {path}")
        response = client.post("/api/ask", json={"question": "Quelles molécules contient la pilule combinée ?"})
        response.raise_for_status()
        body = response.json()
        assert isinstance(body["entities"], list)
        assert body["intent"] == "molecules_contraceptif"
        assert body["results"], "No ontology results: load the ontology into the configured named graph"
        print(f"OK /api/ask: {len(body['results'])} real graph results")
        if args.crud:
            local_id = "CHECK-" + uuid4().hex[:10]
            created = False
            try:
                response = client.post("/api/profils", json={"identifiant": local_id, "age": 25, "imc": 22.5, "fume": False,
                    "conditions": ["Endometriose"], "pression_systolique": 120, "pression_diastolique": 80})
                response.raise_for_status(); created = True
                stored = next(row for row in client.get("/api/profils").json() if row["id"] == local_id)
                assert stored["editable"] and stored["conditions"] == ["Endometriose"]
                response = client.put(f"/api/profils/{local_id}", json={"age": 26})
                response.raise_for_status()
                stored = next(row for row in client.get("/api/profils").json() if row["id"] == local_id)
                assert stored["age"] == 26 and stored["pression_systolique"] == 120 and stored["conditions"] == ["Endometriose"]
                print("OK profile create/edit and preserved condition/pressure")
            finally:
                if created:
                    response = client.delete(f"/api/profils/{local_id}")
                    response.raise_for_status()
                    print("OK disposable profile removed")


if __name__ == "__main__":
    main()
