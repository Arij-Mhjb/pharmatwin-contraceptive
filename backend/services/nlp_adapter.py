from importlib import import_module
from backend.services.security import validate_select
def translate(question:str)->dict:
    try:
        module=import_module("backend.nlp.translator"); result=module.translate(question)
        if not isinstance(result,dict) or not {"intent","entities","sparql"} <= result.keys(): raise ValueError("incompatible teammate translator")
        if result["sparql"]: validate_select(result["sparql"])
        return result
    except (ImportError, ModuleNotFoundError):
        from backend.ai.pipeline import translate as local_translate
        return local_translate(question)
