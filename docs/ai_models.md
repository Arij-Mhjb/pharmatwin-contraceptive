# Local AI models

The semantic pipeline uses `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (Apache-2.0 model card) on CPU for normalized embeddings. It uses `fr_core_news_sm` (MIT spaCy model) for French tokenization and lemmatization. Runtime inference requires no API key and can operate offline after download.

```bash
python -m spacy download fr_core_news_sm
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
PYTHONPATH=. python backend/ai/evaluation.py
```

Intent matching compares the question with multiple curated French examples and rejects scores below 0.48. Entity linking ranks real ontology labels and IRIs with cosine similarity. The embedding model does not generate SPARQL; verified entities fill controlled templates.

Evaluation scores must be recorded only after the command above is run on the target machine. The lightweight CI does not download model weights. Similarity scores are ranking signals, not clinical probabilities. General spaCy NER is not claimed to be biomedical NER.
