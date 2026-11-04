import re
FORBIDDEN = re.compile(r"\b(INSERT|DELETE|LOAD|CLEAR|CREATE|DROP|COPY|MOVE|ADD|SERVICE|WITH)\b", re.I)
def validate_select(query: str) -> str:
    cleaned = re.sub(r"#[^\n]*", "", query).strip()
    if FORBIDDEN.search(cleaned) or not re.match(r"^(PREFIX\s+[^\n]+\s*)*(SELECT|ASK)\b", cleaned, re.I):
        raise ValueError("Only controlled SELECT/ASK queries are allowed")
    return query
def safe_local_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9_-]{1,100}", value): raise ValueError("Invalid resource identifier")
    return value
def sparql_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", " ") + '"'
