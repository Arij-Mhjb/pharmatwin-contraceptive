import numpy as np
from backend.ai import semantic_embeddings
from backend.ai.intent_classifier import IntentClassifier
def fake_encode(texts):
    out=[]
    for t in texts:
        v=np.array([sum(map(ord,t))%11,len(t)%7,1.0],dtype=float);out.append(v/np.linalg.norm(v))
    return np.array(out)
def test_intent_real_similarity_code(monkeypatch):
    monkeypatch.setattr("backend.ai.intent_classifier.encode",fake_encode)
    c=IntentClassifier(threshold=0);r=c.predict("profils SOPK");assert r["intent"] in c.labels and 0<=r["confidence"]<=1.01
def test_embedding_delegates_to_model(monkeypatch):
    class M:
        def encode(self,texts,normalize_embeddings):assert normalize_embeddings;return [[1.,0.]]*len(texts)
    monkeypatch.setattr(semantic_embeddings,"get_embedding_model",lambda:M());assert semantic_embeddings.encode(["a"]).shape==(1,2)
