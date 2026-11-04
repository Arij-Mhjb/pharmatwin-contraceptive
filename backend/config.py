from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    app_name: str = "PharmaTwin Contraceptive API"
    fuseki_base_url: str = "http://localhost:3030"
    fuseki_dataset: str = "pharmatwin"
    fuseki_timeout: float = 15.0
    ontology_graph: str = "https://pharmatwin.ai/graph/ontology"
    profiles_graph: str = "https://pharmatwin.ai/graph/profiles"
    inferred_graph: str = "https://pharmatwin.ai/graph/inferred"
    namespace: str = "https://pharmatwin.ai/contraceptive#"
    ontology_path: Path = ROOT / "ontology" / "pharmatwin.ttl"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    spacy_model: str = "fr_core_news_sm"
    model_path: str | None = None
    offline_models: bool = False
    ai_enabled: bool = True
    cors_origins: str = "http://localhost:3000"
    max_question_length: int = 500
    result_limit: int = 100
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PHARMATWIN_", extra="ignore")

    @property
    def query_url(self): return f"{self.fuseki_base_url}/{self.fuseki_dataset}/query"
    @property
    def update_url(self): return f"{self.fuseki_base_url}/{self.fuseki_dataset}/update"

@lru_cache
def get_settings() -> Settings:
    return Settings()
