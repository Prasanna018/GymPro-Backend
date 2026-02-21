from pydantic import BaseModel
from typing import Optional


class AttendanceCreate(BaseModel):
    member_id: str
    date: Optional[str] = None   # defaults to today if not provided
    check_in: Optional[str] = None  # HH:MM, defaults to current time


class AttendanceCheckout(BaseModel):
    check_out: Optional[str] = None  # HH:MM, defaults to current time


class AttendanceOut(BaseModel):
    id: str
    member_id: str
    date: str
    check_in: str
    check_out: Optional[str] = None

    class Config:
        populate_by_name = True
