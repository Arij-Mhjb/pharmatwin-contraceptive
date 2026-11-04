from importlib import import_module
from backend.services.security import validate_select
from backend.config import get_settings
from backend.nlp.templates import iri


def _normalize(result):
    entities = result.get("entities", [])
    if isinstance(entities, dict):
        entities = entities.get("matches", [])
    if not isinstance(entities, list):
        raise ValueError("incompatible entity response")
    result = {**result, "entities": entities}
    if result.get("sparql"):
        validate_select(result["sparql"])
    return result
def translate(question:str)->dict:
    try:
        module=import_module("backend.nlp.translator"); result=module.translate(question)
        if not isinstance(result,dict) or not {"intent","entities","sparql"} <= result.keys(): raise ValueError("incompatible teammate translator")
        if result["sparql"]: validate_select(result["sparql"])
        return _normalize(result)
    except (ImportError, ModuleNotFoundError):
        from backend.ai.pipeline import translate as local_translate
        return _normalize(local_translate(question))


def query_dataset_params():
    """Protocol dataset parameters keep RDF graph selection out of NLP logic."""
    settings = get_settings()
    graphs = [settings.ontology_graph, settings.profiles_graph, settings.inferred_graph]
    for graph in graphs:
        iri(graph)  # Validate configurable absolute IRIs.
    return [("default-graph-uri", graph) for graph in graphs]
