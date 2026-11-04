from datetime import date, datetime
from decimal import Decimal
from typing import Any
import httpx
from backend.config import Settings, get_settings

class SparqlError(RuntimeError): pass

def _value(binding: dict) -> Any:
    value, datatype = binding.get("value"), binding.get("datatype", "")
    try:
        if datatype.endswith(("#integer", "#int", "#long")): return int(value)
        if datatype.endswith(("#decimal", "#double", "#float")): return float(value)
        if datatype.endswith("#boolean"): return value.lower() == "true"
        if datatype.endswith("#date"): return date.fromisoformat(value).isoformat()
        if datatype.endswith("#dateTime"): return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except (ValueError, TypeError, Decimal.InvalidOperation):
        pass
    return value

class SparqlClient:
    def __init__(self, settings: Settings | None = None, transport=None):
        self.settings = settings or get_settings(); self.transport = transport

    def run_select(self, query: str) -> list[dict]:
        try:
            with httpx.Client(timeout=self.settings.fuseki_timeout, transport=self.transport) as client:
                r = client.post(self.settings.query_url, data={"query": query}, headers={"Accept": "application/sparql-results+json"})
                r.raise_for_status(); data = r.json()
            if "boolean" in data:
                return [{"boolean": bool(data["boolean"])}] if data["boolean"] else []
            return [{k: _value(v) for k, v in row.items()} for row in data.get("results", {}).get("bindings", [])]
        except (httpx.HTTPError, ValueError) as exc: raise SparqlError(f"Fuseki query failed: {exc}") from exc

    def run_update(self, update: str) -> None:
        try:
            with httpx.Client(timeout=self.settings.fuseki_timeout, transport=self.transport) as client:
                r = client.post(self.settings.update_url, data={"update": update}); r.raise_for_status()
        except httpx.HTTPError as exc: raise SparqlError(f"Fuseki update failed: {exc}") from exc

def run_select(query: str) -> list[dict]: return SparqlClient().run_select(query)
def run_update(update: str) -> None: SparqlClient().run_update(update)
