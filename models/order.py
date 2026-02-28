from pydantic import BaseModel
from typing import List, Literal, Optional


class OrderItem(BaseModel):
    supplement_id: str
    quantity: int
    price: float


class OrderCreate(BaseModel):
    items: List[OrderItem]


class OrderOut(BaseModel):
    id: str
    member_id: str
    items: List[OrderItem]
    total: float
    date: str
    status: str
    payment_status: Optional[str] = "pending"  # pending, paid
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None

    class Config:
        populate_by_name = True
