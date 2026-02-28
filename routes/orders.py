from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from models.order import OrderCreate, OrderOut, OrderItem
from auth import require_owner, get_current_user
from bson import ObjectId
from datetime import date
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])


def order_doc_to_out(doc: dict) -> OrderOut:
    items = [OrderItem(**item) for item in doc.get("items", [])]
    return OrderOut(
        id=str(doc["_id"]),
        member_id=doc["member_id"],
        items=items,
        total=doc["total"],
        date=doc["date"],
        status=doc["status"],
        payment_status=doc.get("payment_status", "pending"),
        razorpay_order_id=doc.get("razorpay_order_id"),
        razorpay_payment_id=doc.get("razorpay_payment_id"),
    )


@router.get("", response_model=List[OrderOut])
async def list_orders(_owner=Depends(require_owner)):
    db = get_db()
    orders = await db.orders.find({"owner_id": _owner["owner_id"]}).sort("date", -1).to_list(1000)
    return [order_doc_to_out(o) for o in orders]


@router.get("/me", response_model=List[OrderOut])
async def my_orders(current_user: dict = Depends(get_current_user)):
    db = get_db()
    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")
    orders = await db.orders.find({"member_id": str(member["_id"])}).sort("date", -1).to_list(100)
    return [order_doc_to_out(o) for o in orders]


@router.post("", response_model=OrderOut, status_code=201)
async def place_order(body: OrderCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()

    # Get member
    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")
    member_id = str(member["_id"])

    # Validate items and compute total
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
            "quantity": item.quantity,
            "price": supplement["price"],
        })
        total += supplement["price"] * item.quantity
        # Reduce stock
        await db.supplements.update_one({"_id": sid}, {"$inc": {"stock": -item.quantity}})

    order_doc = {
        "owner_id": current_user["owner_id"],
        "member_id": member_id,
        "items": validated_items,
        "total": round(total, 2),
        "date": date.today().isoformat(),
        "status": "pending",
    }
    result = await db.orders.insert_one(order_doc)
    order_doc["_id"] = result.inserted_id
    return order_doc_to_out(order_doc)
