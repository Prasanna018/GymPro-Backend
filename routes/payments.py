from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db
from models.payment import PaymentCreate, PaymentOut
from auth import require_owner, get_current_user
from bson import ObjectId
from datetime import date
from typing import Optional, List
import random
import string

router = APIRouter(prefix="/payments", tags=["Payments"])


def generate_invoice_id() -> str:
    today = date.today()
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"INV-{today.year}-{rand}"


def payment_doc_to_out(doc: dict) -> PaymentOut:
    return PaymentOut(
        id=str(doc["_id"]),
        member_id=doc["member_id"],
        amount=doc["amount"],
        date=doc["date"],
        status=doc["status"],
        plan_id=doc["plan_id"],
        method=doc.get("method", "Cash"),
        invoice_id=doc.get("invoice_id"),
    )


@router.get("", response_model=List[PaymentOut])
async def list_payments(
    status_filter: Optional[str] = Query(None, alias="status"),
    member_id: Optional[str] = Query(None),
    _owner=Depends(require_owner),
):
    db = get_db()
    query = {"owner_id": _owner["owner_id"]}
    if status_filter and status_filter != "all":
        query["status"] = status_filter
    if member_id:
        query["member_id"] = member_id
    payments = await db.payments.find(query).sort("date", -1).to_list(1000)
    return [payment_doc_to_out(p) for p in payments]


@router.get("/me", response_model=List[PaymentOut])
async def my_payments(current_user: dict = Depends(get_current_user)):
    db = get_db()
    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")
    payments = await db.payments.find({"member_id": str(member["_id"])}).sort("date", -1).to_list(100)
    return [payment_doc_to_out(p) for p in payments]


@router.post("", response_model=PaymentOut, status_code=201)
async def create_payment(body: PaymentCreate, _owner=Depends(require_owner)):
    db = get_db()
    try:
        mid = ObjectId(body.member_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid member ID")

    member = await db.members.find_one({"_id": mid, "owner_id": _owner["owner_id"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    invoice_id = generate_invoice_id()
    payment_doc = {
        "owner_id": _owner["owner_id"],
        "member_id": body.member_id,
        "amount": body.amount,
        "date": date.today().isoformat(),
        "status": "paid",
        "plan_id": body.plan_id,
        "method": body.method or "Cash",
        "invoice_id": invoice_id,
    }
    result = await db.payments.insert_one(payment_doc)

    # Update member's paid/due amounts
    await db.members.update_one(
        {"_id": mid},
        {
            "$inc": {"paid_amount": body.amount},
            "$set": {"due_amount": max(0, member.get("due_amount", 0) - body.amount)}
        }
    )
    payment_doc["_id"] = result.inserted_id
    return payment_doc_to_out(payment_doc)


@router.put("/{payment_id}/collect", response_model=PaymentOut)
async def collect_payment(payment_id: str, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(payment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payment ID")

    payment = await db.payments.find_one({"_id": oid, "owner_id": _owner["owner_id"]})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment["status"] == "paid":
        raise HTTPException(status_code=400, detail="Payment already marked as paid")

    invoice_id = generate_invoice_id()
    result = await db.payments.find_one_and_update(
        {"_id": oid, "owner_id": _owner["owner_id"]},
        {"$set": {"status": "paid", "invoice_id": invoice_id, "date": date.today().isoformat()}},
        return_document=True,
    )
    # Update member
    try:
        mid = ObjectId(payment["member_id"])
        member = await db.members.find_one({"_id": mid})
        if member:
            await db.members.update_one(
                {"_id": mid},
                {
                    "$inc": {"paid_amount": payment["amount"]},
                    "$set": {"due_amount": max(0, member.get("due_amount", 0) - payment["amount"])}
                }
            )
    except Exception:
        pass
    return payment_doc_to_out(result)
