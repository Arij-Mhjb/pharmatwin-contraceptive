from pathlib import Path
import json,numpy as np
from backend.ai.ontology_index import OntologyIndex
i=OntologyIndex();out=Path(__file__).resolve().parents[1]/"ai/index";out.mkdir(exist_ok=True);np.save(out/"embeddings.npy",i.matrix);(out/"items.json").write_text(json.dumps(i.items,ensure_ascii=False,indent=2),encoding="utf-8");print(len(i.items),"resources indexed")
