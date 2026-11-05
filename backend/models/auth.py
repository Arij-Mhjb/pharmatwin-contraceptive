from typing import Literal
from pydantic import BaseModel, Field, field_validator
import re

EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

class Credentials(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str):
        value = value.strip().lower()
        if not EMAIL.fullmatch(value):
            raise ValueError("Adresse e-mail invalide")
        return value

class SignUp(Credentials):
    display_name: str = Field(min_length=2, max_length=80)

class SignIn(Credentials):
    pass

class Onboarding(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)
    academic_use_accepted: bool

class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)

class AvatarUpdate(BaseModel):
    data_url: str | None = Field(default=None, max_length=2_100_000)

    @field_validator("data_url")
    @classmethod
    def valid_image(cls, value: str | None):
        if value is not None and not re.match(r"^data:image/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$", value):
            raise ValueError("Format d’image invalide (JPEG, PNG ou WebP attendu)")
        return value

class UserAdminUpdate(BaseModel):
    role: Literal["user", "admin"] | None = None
    status: Literal["active", "disabled"] | None = None
