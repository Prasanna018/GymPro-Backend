from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from auth import require_owner
from pydantic import BaseModel
from typing import List
from datetime import date

router = APIRouter(prefix="/reminders", tags=["Reminders"])


class ReminderRequest(BaseModel):
    member_ids: List[str]


@router.get("/pending")
async def get_pending_reminders(_owner=Depends(require_owner)):
    """Returns members with expiry within 7 days OR pending dues."""
    db = get_db()
    today = date.today()
    week_later = date.today().replace(
        day=min(today.day + 7, 28)
    ).isoformat()

    members = await db.members.find({"owner_id": _owner["owner_id"]}).to_list(1000)
    pending = []
    for member in members:
        expiry = member.get("expiry_date", "")
        due = member.get("due_amount", 0)
        days_until_expiry = None
        if expiry:
            try:
                exp_date = date.fromisoformat(expiry)
                days_until_expiry = (exp_date - today).days
            except Exception:
                pass

        needs_reminder = (
            (days_until_expiry is not None and days_until_expiry <= 7) or
            (due > 0)
        )
        if needs_reminder:
            plan = None
            if member.get("plan_id"):
                try:
                    from bson import ObjectId
                    plan_doc = await db.plans.find_one({"_id": ObjectId(member["plan_id"])})
                    if plan_doc:
                        plan = plan_doc.get("name")
                except Exception:
                    pass
            pending.append({
                "id": str(member["_id"]),
                "name": member["name"],
                "email": member["email"],
                "phone": member.get("phone", ""),
                "plan": plan,
                "expiry_date": expiry,
                "days_until_expiry": days_until_expiry,
                "due_amount": due,
                "payment_status": "pending" if due > 0 else "paid",
            })
    return pending


@router.post("/email")
async def send_email_reminders(body: ReminderRequest, _owner=Depends(require_owner)):
    """Stub: log email reminders. Wire SMTP in production."""
    if not body.member_ids:
        raise HTTPException(status_code=400, detail="No member IDs provided")
    # In production, integrate with SMTP / SendGrid / etc.
    print(f"[EMAIL] Sending reminders to: {body.member_ids}")
    return {
        "message": f"Email reminders sent to {len(body.member_ids)} member(s)",
        "member_ids": body.member_ids,
    }


@router.post("/whatsapp")
async def send_whatsapp_reminders(body: ReminderRequest, _owner=Depends(require_owner)):
    """Stub: log WhatsApp reminders. Wire Twilio in production."""
    if not body.member_ids:
        raise HTTPException(status_code=400, detail="No member IDs provided")
    # In production, integrate with Twilio / WhatsApp Business API
    print(f"[WHATSAPP] Sending reminders to: {body.member_ids}")
    return {
        "message": f"WhatsApp reminders sent to {len(body.member_ids)} member(s)",
        "member_ids": body.member_ids,
    }
