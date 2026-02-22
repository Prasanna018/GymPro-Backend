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
    """Sends real email reminders to selected members."""
    if not body.member_ids:
        raise HTTPException(status_code=400, detail="No member IDs provided")
    
    db = get_db()
    from bson import ObjectId
    from email_utils import send_reminder_email
    
    success_count = 0
    failed_names = []
    
    for m_id in body.member_ids:
        try:
            member = await db.members.find_one({"_id": ObjectId(m_id), "owner_id": _owner["owner_id"]})
            if not member:
                continue
            
            name = member.get("name", "Member")
            email = member.get("email")
            due = member.get("due_amount", 0)
            expiry = member.get("expiry_date", "N/A")
            
            if not email:
                failed_names.append(f"{name} (No Email)")
                continue

            # Construct professional message
            if due > 0:
                subject = "Payment Reminder: GymPro Membership"
                message = f"We noticed a pending balance of ₹{due} on your account. Please visit the gym to settle your dues and continue enjoying your workouts!"
            else:
                subject = "Membership Expiry Reminder"
                message = f"Your current membership plan is set to expire on {expiry}. Renew today to maintain your progress without interruption!"

            sent = await send_reminder_email(
                to_email=email,
                member_name=name,
                subject=subject,
                message_text=message
            )
            
            if sent:
                success_count += 1
            else:
                failed_names.append(name)
                
        except Exception as e:
            print(f"Error processing reminder for {m_id}: {str(e)}")
            continue

    return {
        "message": f"Reminders sent successfully to {success_count} member(s).",
        "failed": failed_names,
        "success_count": success_count
    }
