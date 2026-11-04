import numpy as np
from .model_loader import get_embedding_model
def encode(texts): return np.asarray(get_embedding_model().encode(texts, normalize_embeddings=True),dtype=np.float32)
def similarities(query, corpus): return encode([query]) @ encode(corpus).T
