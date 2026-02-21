from pydantic import BaseModel
from typing import List, Optional


class PlanCreate(BaseModel):
    name: str
    duration: int  # months
    price: float
    features: List[str] = []


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    features: Optional[List[str]] = None


class PlanOut(BaseModel):
    id: str
    name: str
    duration: int
    price: float
    features: List[str] = []

    class Config:
        populate_by_name = True
