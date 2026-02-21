from pydantic import BaseModel
from typing import Optional


class SupplementCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int
    category: str
    image: Optional[str] = None


class SupplementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    image: Optional[str] = None


class SupplementOut(BaseModel):
    id: str
    name: str
    description: str
    price: float
    stock: int
    category: str
    image: Optional[str] = None

    class Config:
        populate_by_name = True
