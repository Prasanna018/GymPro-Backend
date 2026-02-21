from pydantic import BaseModel
from typing import Optional, Literal


class PaymentCreate(BaseModel):
    member_id: str
    amount: float
    plan_id: str
    method: Optional[str] = "Cash"  # Cash, UPI, Card, etc.


class PaymentUpdate(BaseModel):
    status: Optional[Literal["paid", "pending", "overdue"]] = None
    method: Optional[str] = None


class PaymentOut(BaseModel):
    id: str
    member_id: str
    amount: float
    date: str
    status: str
    plan_id: str
    method: Optional[str] = "Cash"
    invoice_id: Optional[str] = None

    class Config:
        populate_by_name = True
