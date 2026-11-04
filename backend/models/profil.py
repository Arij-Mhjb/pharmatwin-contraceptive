from pydantic import BaseModel, Field, field_validator, model_validator

class ProfilBase(BaseModel):
    identifiant: str = Field(pattern=r"^[A-Za-z0-9_-]{2,50}$")
    age: int = Field(ge=12, le=100)
    imc: float = Field(gt=8, lt=80)
    pression_systolique: int | None = Field(default=None, ge=50, le=260)
    pression_diastolique: int | None = Field(default=None, ge=30, le=180)
    fume: bool = False
    conditions: list[str] = Field(default_factory=list, max_length=30)
    @field_validator("conditions")
    @classmethod
    def valid_ids(cls, values):
        import re
        if any(not re.fullmatch(r"[A-Za-zÀ-ÿ0-9_-]{1,100}", v) for v in values): raise ValueError("invalid condition identifier")
        return list(dict.fromkeys(values))
    @model_validator(mode="after")
    def pressure(self):
        if self.pression_systolique and self.pression_diastolique and self.pression_diastolique >= self.pression_systolique:
            raise ValueError("diastolic pressure must be lower than systolic pressure")
        return self

class ProfilCreate(ProfilBase): pass
class ProfilUpdate(BaseModel):
    age: int | None = Field(default=None, ge=12, le=100)
    imc: float | None = Field(default=None, gt=8, lt=80)
    pression_systolique: int | None = Field(default=None, ge=50, le=260)
    pression_diastolique: int | None = Field(default=None, ge=30, le=180)
    fume: bool | None = None
    conditions: list[str] | None = Field(default=None, max_length=30)
    @model_validator(mode="after")
    def valid_update(self):
        supplied = self.model_fields_set
        if any(getattr(self, key) is None for key in supplied - {"pression_systolique", "pression_diastolique"}):
            raise ValueError("Required fields cannot be set to null")
        if self.conditions is not None:
            self.conditions = ProfilBase.valid_ids(self.conditions)
        return self

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
