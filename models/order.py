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

    class Config:
        populate_by_name = True
