from pydantic import BaseModel
class AskResponse(BaseModel):
    intent: str
    entities: dict | list[dict]
    sparql: str
    results: list[dict]
