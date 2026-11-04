"""Patient workspace data, composed with the existing clinical profile model."""
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field
from backend.models.profil import ProfilCreate

class Preferences(BaseModel):
    forms: list[str] = Field(default_factory=list, max_length=15)
    hormones: Literal["indifferent", "avoid", "accept"] = "indifferent"
    benefits: list[str] = Field(default_factory=list, max_length=15)
    avoid_effects: list[str] = Field(default_factory=list, max_length=15)

class PastUse(BaseModel):
    method_id: str = Field(min_length=1, max_length=100)
    period: str = Field(default="", max_length=80)
    experience: Literal["positive", "negative", "unknown"] = "unknown"
    notes: str = Field(default="", max_length=500)

class Symptom(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    date: date
    severity: Literal["leger", "modere", "important"] = "leger"
    notes: str = Field(default="", max_length=500)

class PatientInput(BaseModel):
    display_name: str = Field(min_length=1, max_length=60)
    profile: ProfilCreate
    preferences: Preferences = Field(default_factory=Preferences)
    current_method: str | None = None
    medications: list[str] = Field(default_factory=list, max_length=30)
    other_medications: str = Field(default="", max_length=500)
    other_conditions: str = Field(default="", max_length=1000)
    history: list[PastUse] = Field(default_factory=list, max_length=30)
    symptoms: list[Symptom] = Field(default_factory=list, max_length=100)
    history_complete: bool = False

class SymptomInput(BaseModel):
    observation: Symptom
