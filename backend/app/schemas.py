from typing import Any
from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    display_name: str = Field(min_length=2, max_length=80)
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_]+$")

    @field_validator("display_name")
    @classmethod
    def display_name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Display name must contain at least two non-space characters.")
        return value


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class EmailInput(BaseModel):
    email: EmailStr


class VerifyEmailInput(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class ResetPasswordInput(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=10, max_length=128)


class ChangePasswordInput(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class ChangeEmailInput(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_email: EmailStr


class AccountDeleteInput(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class AvatarUpdate(BaseModel):
    avatar: dict = Field(default_factory=dict)
    theme: str = Field(default="dark", pattern=r"^(dark|light|system)$")
    display_name: str | None = Field(default=None, min_length=2, max_length=80)
    username: str | None = Field(
        default=None, min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_]+$"
    )


class PaymentCreateInput(BaseModel):
    plan_id: str = Field(pattern=r"^(pro|max|full_access)$")


class PaymentVerifyInput(BaseModel):
    plan_id: str = Field(pattern=r"^full_access$")
    razorpay_order_id: str = Field(min_length=4, max_length=100)
    razorpay_payment_id: str = Field(min_length=4, max_length=100)
    razorpay_signature: str = Field(min_length=16, max_length=300)


class ProgressUpdate(BaseModel):
    time_spent_seconds: int = Field(default=0, ge=0, le=86_400)
    timezone: str = Field(default="UTC", min_length=1, max_length=80)


class ExerciseSubmission(BaseModel):
    answer: Any = None
    source_code: str | None = Field(default=None, max_length=100_000)
    timezone: str = Field(default="UTC", min_length=1, max_length=80)
