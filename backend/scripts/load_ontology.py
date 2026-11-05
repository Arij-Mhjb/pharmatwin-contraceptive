from pathlib import Path
import httpx
from backend.config import get_settings


def main() -> None:
    s = get_settings()
    data = Path(s.ontology_path).read_bytes()
    url = f"{s.fuseki_base_url}/{s.fuseki_dataset}/data"
    response = httpx.put(
        url,
        params={"graph": s.ontology_graph},
        content=data,
        headers={"Content-Type": "text/turtle"},
        auth=s.fuseki_auth,
        timeout=60,
    )
    response.raise_for_status()
    print("Ontology loaded", len(data), "bytes", flush=True)


if __name__ == "__main__":
    main()
