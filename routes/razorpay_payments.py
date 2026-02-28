"""
Razorpay Payment Integration Routes
Uses httpx (already in requirements) to call Razorpay REST API directly —
bypassing the razorpay SDK which has a Python 3.13 incompatibility.
"""

import hmac
import hashlib
import os
import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from datetime import date
from database import get_db
from auth import get_current_user
from models.payment import PaymentOut
from models.order import OrderItem, OrderOut
import random
import string

router = APIRouter(prefix="/razorpay", tags=["Razorpay"])

RAZORPAY_API_URL = "https://api.razorpay.com/v1"


def _get_credentials():
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not key_id or "YOUR_KEY" in key_id:
        raise HTTPException(
            status_code=500,
            detail="Razorpay keys not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env"
        )
    return key_id, key_secret


async def _create_razorpay_order(amount_paise: int, receipt: str, notes: dict) -> dict:
    """Call Razorpay Orders API to create a new order."""
    key_id, key_secret = _get_credentials()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{RAZORPAY_API_URL}/orders",
            auth=(key_id, key_secret),
            json={
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "notes": notes,
            },
            timeout=15,
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Razorpay error: {resp.text}")
    return resp.json()


def generate_invoice_id() -> str:
    today = date.today()
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"INV-{today.year}-{rand}"


def verify_signature(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> bool:
    """Verify Razorpay payment signature using HMAC SHA256."""
    _, key_secret = _get_credentials()
    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_signature = hmac.new(
        key_secret.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(generated_signature, razorpay_signature)


# ─── Request/Response Models ────────────────────────────────────────────────

class MembershipOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int
    currency: str
    key_id: str
    member_name: str
    member_email: str


class VerifyMembershipPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    amount: float
    plan_id: str


class StoreOrderRequest(BaseModel):
    items: List[OrderItem]


class StoreOrderResponse(BaseModel):
    razorpay_order_id: str
    amount: int
    currency: str
    key_id: str
    member_name: str
    member_email: str
    validated_items: List[dict]


class VerifyStorePaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    items: List[OrderItem]
    total: float


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/key")
async def get_razorpay_key():
    """Return the Razorpay public key ID (no auth required)."""
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    if not key_id or "YOUR_KEY" in key_id:
        raise HTTPException(status_code=500, detail="Razorpay not configured")
    return {"key_id": key_id}


@router.post("/create-membership-order", response_model=MembershipOrderResponse)
async def create_membership_order(current_user: dict = Depends(get_current_user)):
    """Create a Razorpay order for the member's pending membership due."""
    db = get_db()
    key_id, _ = _get_credentials()

    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")

    due_amount = member.get("due_amount", 0)
    if due_amount <= 0:
        raise HTTPException(status_code=400, detail="No pending dues found")

    amount_paise = int(due_amount * 100)
    order_data = await _create_razorpay_order(
        amount_paise=amount_paise,
        receipt=f"membership_{str(member['_id'])}_{date.today().isoformat()}",
        notes={"member_id": str(member["_id"]), "purpose": "membership_fee"},
    )

    return MembershipOrderResponse(
        razorpay_order_id=order_data["id"],
        amount=amount_paise,
        currency="INR",
        key_id=key_id,
        member_name=member.get("name", ""),
        member_email=member.get("email", ""),
    )


@router.post("/verify-membership-payment", response_model=PaymentOut)
async def verify_membership_payment(
    body: VerifyMembershipPaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify payment signature and record the membership payment in DB."""
    db = get_db()

    if not verify_signature(body.razorpay_order_id, body.razorpay_payment_id, body.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature. Verification failed.")

    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")

    invoice_id = generate_invoice_id()
    payment_doc = {
        "owner_id": current_user["owner_id"],
        "member_id": str(member["_id"]),
        "amount": body.amount,
        "date": date.today().isoformat(),
        "status": "paid",
        "plan_id": body.plan_id,
        "method": "Online (Razorpay)",
        "invoice_id": invoice_id,
        "razorpay_order_id": body.razorpay_order_id,
        "razorpay_payment_id": body.razorpay_payment_id,
    }
    result = await db.payments.insert_one(payment_doc)

    # Clear member's due amount
    await db.members.update_one(
        {"_id": member["_id"]},
        {
            "$inc": {"paid_amount": body.amount},
            "$set": {"due_amount": 0},
        }
    )

    payment_doc["_id"] = result.inserted_id
    return PaymentOut(
        id=str(payment_doc["_id"]),
        member_id=payment_doc["member_id"],
        amount=payment_doc["amount"],
        date=payment_doc["date"],
        status=payment_doc["status"],
        plan_id=payment_doc["plan_id"],
        method=payment_doc["method"],
        invoice_id=payment_doc["invoice_id"],
        razorpay_order_id=payment_doc["razorpay_order_id"],
        razorpay_payment_id=payment_doc["razorpay_payment_id"],
    )


@router.post("/create-store-order", response_model=StoreOrderResponse)
async def create_store_order(
    body: StoreOrderRequest,
    current_user: dict = Depends(get_current_user)
):
    """Validate cart items & create a Razorpay order for a store purchase."""
    db = get_db()
    key_id, _ = _get_credentials()

    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")

    if not body.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    validated_items = []
    total = 0.0
    for item in body.items:
        try:
            sid = ObjectId(item.supplement_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid supplement ID: {item.supplement_id}")

        supplement = await db.supplements.find_one({"_id": sid, "owner_id": current_user["owner_id"]})
        if not supplement:
            raise HTTPException(status_code=404, detail=f"Supplement {item.supplement_id} not found")
        if supplement["stock"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {supplement['name']}. Available: {supplement['stock']}"
            )
        validated_items.append({
            "supplement_id": item.supplement_id,
            "name": supplement["name"],
            "quantity": item.quantity,
            "price": supplement["price"],
        })
        total += supplement["price"] * item.quantity

    total = round(total, 2)
    amount_paise = int(total * 100)
    order_data = await _create_razorpay_order(
        amount_paise=amount_paise,
        receipt=f"store_{str(member['_id'])}_{date.today().isoformat()}",
        notes={"member_id": str(member["_id"]), "purpose": "store_purchase"},
    )

    return StoreOrderResponse(
        razorpay_order_id=order_data["id"],
        amount=amount_paise,
        currency="INR",
        key_id=key_id,
        member_name=member.get("name", ""),
        member_email=member.get("email", ""),
        validated_items=validated_items,
    )


@router.post("/verify-store-payment", response_model=OrderOut)
async def verify_store_payment(
    body: VerifyStorePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify signature, deduct stock, and record the store order as paid."""
    db = get_db()

    if not verify_signature(body.razorpay_order_id, body.razorpay_payment_id, body.razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid payment signature. Order not fulfilled.")

    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")

    final_items = []
    for item in body.items:
        try:
            sid = ObjectId(item.supplement_id)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid supplement ID: {item.supplement_id}")

        supplement = await db.supplements.find_one({"_id": sid, "owner_id": current_user["owner_id"]})
        if not supplement:
            raise HTTPException(status_code=404, detail=f"Supplement {item.supplement_id} not found")
        if supplement["stock"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {supplement['name']}.")

        await db.supplements.update_one({"_id": sid}, {"$inc": {"stock": -item.quantity}})
        final_items.append({
            "supplement_id": item.supplement_id,
            "quantity": item.quantity,
            "price": supplement["price"],
        })

    order_doc = {
        "owner_id": current_user["owner_id"],
        "member_id": str(member["_id"]),
        "items": final_items,
        "total": round(body.total, 2),
        "date": date.today().isoformat(),
        "status": "completed",
        "payment_status": "paid",
        "razorpay_order_id": body.razorpay_order_id,
        "razorpay_payment_id": body.razorpay_payment_id,
    }
    result = await db.orders.insert_one(order_doc)
    order_doc["_id"] = result.inserted_id

    from models.order import OrderItem as OI
    return OrderOut(
        id=str(order_doc["_id"]),
        member_id=order_doc["member_id"],
        items=[OI(**i) for i in order_doc["items"]],
        total=order_doc["total"],
        date=order_doc["date"],
        status=order_doc["status"],
        payment_status=order_doc["payment_status"],
        razorpay_order_id=order_doc["razorpay_order_id"],
        razorpay_payment_id=order_doc["razorpay_payment_id"],
    )
