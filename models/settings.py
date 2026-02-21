from pydantic import BaseModel
from typing import Optional


class NotificationSettings(BaseModel):
    email_reminders: bool = True
    whatsapp_reminders: bool = True
    payment_alerts: bool = True
    expiry_alerts: bool = True
    daily_reports: bool = False


class GymSettingsUpdate(BaseModel):
    gym_name: Optional[str] = None
    owner_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    opening_time: Optional[str] = None
    closing_time: Optional[str] = None
    notifications: Optional[NotificationSettings] = None


class GymSettingsOut(BaseModel):
    gym_name: str = "GymPro Fitness Center"
    owner_name: str = "Admin"
    email: str = "owner@gympro.com"
    phone: str = ""
    address: str = ""
    opening_time: str = "06:00"
    closing_time: str = "22:00"
    notifications: NotificationSettings = NotificationSettings()

    class Config:
        populate_by_name = True
