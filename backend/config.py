from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    app_name: str = "PharmaTwin Contraceptive API"
    fuseki_base_url: str = "http://localhost:3030"
    fuseki_dataset: str = "pharmatwin"
    fuseki_timeout: float = 15.0
    fuseki_username: str | None = "admin"
    fuseki_password: SecretStr | None = SecretStr("admin")
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
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3100,http://127.0.0.1:3100"
    max_question_length: int = 500
    result_limit: int = 100
    patient_store_path: Path = ROOT / "backend" / "data" / "patient.sqlite3"
    session_days: int = 7
    cookie_secure: bool = False
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: SecretStr | None = None
    bootstrap_admin_name: str = "Administrateur PharmaTwin"
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PHARMATWIN_", extra="ignore")

    @property
    def fuseki_auth(self):
        if self.fuseki_username and self.fuseki_password:
            return (self.fuseki_username, self.fuseki_password.get_secret_value())
        return None

    @property
    def query_url(self): return f"{self.fuseki_base_url}/{self.fuseki_dataset}/query"
    @property
    def update_url(self): return f"{self.fuseki_base_url}/{self.fuseki_dataset}/update"

@lru_cache
def get_settings() -> Settings:
    return Settings()
