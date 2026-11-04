from pydantic import BaseModel
class AskResponse(BaseModel):
    intent: str
    entities: list[dict]
    sparql: str
    results: list[dict]
