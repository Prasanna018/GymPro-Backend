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
    member_name: Optional[str] = None
    date: str
    check_in: str
    check_out: Optional[str] = None

    class Config:
        populate_by_name = True


class AttendanceStats(BaseModel):
    total_active_members: int
    present_today: int
    absent_today: int
    attendance_rate_today: float       # %
    attendance_rate_30d: float         # % over last 30 days
    peak_hour: Optional[str] = None    # e.g. "07:00"
