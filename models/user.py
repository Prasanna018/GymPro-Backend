from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from bson import ObjectId


def str_object_id(v):
    return str(v) if isinstance(v, ObjectId) else v


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["owner", "member"] = "member"
    phone: Optional[str] = None
    avatar: Optional[str] = None


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        populate_by_name = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
