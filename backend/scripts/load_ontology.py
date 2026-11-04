from pathlib import Path
import httpx
from backend.config import get_settings
s=get_settings();data=Path(s.ontology_path).read_bytes();url=f"{s.fuseki_base_url}/{s.fuseki_dataset}/data"
r=httpx.put(url,params={"graph":s.ontology_graph},content=data,headers={"Content-Type":"text/turtle"},timeout=60);r.raise_for_status();print("Ontology loaded",len(data),"bytes")
