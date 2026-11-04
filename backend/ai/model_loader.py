from functools import lru_cache
from backend.config import get_settings
@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    s=get_settings(); return SentenceTransformer(s.model_path or s.embedding_model, device="cpu", local_files_only=s.offline_models)
@lru_cache(maxsize=1)
def get_spacy_model():
    import spacy
    try: return spacy.load(get_settings().spacy_model)
    except OSError: return spacy.blank("fr")
