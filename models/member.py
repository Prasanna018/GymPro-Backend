from pydantic import BaseModel, EmailStr
from typing import Optional, Literal


class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    address: str
    plan_id: str
    # Member extra fields
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    avatar: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    plan_id: Optional[str] = None
    status: Optional[Literal["active", "expired", "pending"]] = None
    due_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None
    avatar: Optional[str] = None
    password: Optional[str] = None


class MemberSelfUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None


class MemberOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    address: str
    joining_date: str
    expiry_date: str
    plan_id: str
    status: str
    avatar: Optional[str] = None
    due_amount: float = 0
    paid_amount: float = 0
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal: Optional[str] = None

    class Config:
        populate_by_name = True
