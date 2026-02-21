from fastapi import APIRouter, HTTPException, Depends, Query, status
from database import get_db
from models.member import MemberCreate, MemberUpdate, MemberSelfUpdate, MemberOut
from auth import get_current_user, require_owner, get_password_hash
from bson import ObjectId
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Optional, List

router = APIRouter(prefix="/members", tags=["Members"])


def member_doc_to_out(doc: dict) -> MemberOut:
    return MemberOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        phone=doc["phone"],
        address=doc["address"],
        joining_date=doc["joining_date"],
        expiry_date=doc["expiry_date"],
        plan_id=doc["plan_id"],
        status=doc["status"],
        avatar=doc.get("avatar"),
        due_amount=doc.get("due_amount", 0),
        paid_amount=doc.get("paid_amount", 0),
        emergency_contact=doc.get("emergency_contact"),
        blood_group=doc.get("blood_group"),
        height=doc.get("height"),
        weight=doc.get("weight"),
        goal=doc.get("goal"),
    )


@router.get("", response_model=List[MemberOut])
async def list_members(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    _owner=Depends(require_owner)
):
    db = get_db()
    query = {"owner_id": _owner["owner_id"]}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    if status_filter and status_filter != "all":
        query["status"] = status_filter

    # Auto-update expired statuses
    today = date.today().isoformat()
    await db.members.update_many(
        {"expiry_date": {"$lt": today}, "status": "active", "owner_id": _owner["owner_id"]},
        {"$set": {"status": "expired"}}
    )

    members = await db.members.find(query).sort("name", 1).to_list(1000)
    return [member_doc_to_out(m) for m in members]


@router.post("", response_model=MemberOut, status_code=201)
async def create_member(body: MemberCreate, _owner=Depends(require_owner)):
    db = get_db()

    # Check duplicate email across whole system (since email is used for login)
    existing = await db.members.find_one({"email": body.email})
    if existing:
        raise HTTPException(status_code=400, detail="Member with this email already exists")

    # Fetch plan for auto-computation
    plan = await db.plans.find_one({"_id": ObjectId(body.plan_id), "owner_id": _owner["owner_id"]})
    if not plan:
        raise HTTPException(status_code=404, detail="Membership plan not found")

    today = date.today()
    try:
        from dateutil.relativedelta import relativedelta
        expiry = today + relativedelta(months=plan["duration"])
    except Exception:
        expiry = today

    member_doc = {
        "owner_id": _owner["owner_id"],
        "name": body.name,
        "email": body.email,
        "phone": body.phone,
        "address": body.address,
        "plan_id": body.plan_id,
        "joining_date": today.isoformat(),
        "expiry_date": expiry.isoformat(),
        "status": "active",
        "due_amount": plan["price"],
        "paid_amount": 0,
        "emergency_contact": body.emergency_contact,
        "blood_group": body.blood_group,
        "height": body.height,
        "weight": body.weight,
        "goal": body.goal,
        "avatar": body.avatar,
        "created_at": datetime.utcnow(),
    }
    result = await db.members.insert_one(member_doc)

    # Create a user account for the member so they can log in
    existing_user = await db.users.find_one({"email": body.email})
    if not existing_user:
        await db.users.insert_one({
            "_id": result.inserted_id,  # same ID as member doc
            "name": body.name,
            "email": body.email,
            "hashed_password": get_password_hash(body.password),
            "role": "member",
            "phone": body.phone,
            "owner_id": _owner["owner_id"]
        })

    member_doc["_id"] = result.inserted_id
    return member_doc_to_out(member_doc)


@router.get("/me", response_model=MemberOut)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    db = get_db()
    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")
    return member_doc_to_out(member)


@router.put("/me", response_model=MemberOut)
async def update_my_profile(body: MemberSelfUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    result = await db.members.find_one_and_update(
        {"email": current_user["email"]},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Member not found")
    return member_doc_to_out(result)


@router.get("/{member_id}", response_model=MemberOut)
async def get_member(member_id: str, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(member_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid member ID")
    member = await db.members.find_one({"_id": oid, "owner_id": _owner["owner_id"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member_doc_to_out(member)


@router.put("/{member_id}", response_model=MemberOut)
async def update_member(member_id: str, body: MemberUpdate, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(member_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid member ID")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}

    # If plan changed, recalculate expiry date
    if "plan_id" in update_data:
        plan = await db.plans.find_one({"_id": ObjectId(update_data["plan_id"]), "owner_id": _owner["owner_id"]})
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        member = await db.members.find_one({"_id": oid, "owner_id": _owner["owner_id"]})
        if member:
            try:
                from dateutil.relativedelta import relativedelta
                joining = date.fromisoformat(member["joining_date"])
                update_data["expiry_date"] = (joining + relativedelta(months=plan["duration"])).isoformat()
                update_data["due_amount"] = plan["price"]
                update_data["status"] = "active"
            except Exception:
                pass

    result = await db.members.find_one_and_update(
        {"_id": oid, "owner_id": _owner["owner_id"]},
        {"$set": update_data},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Member not found")
    return member_doc_to_out(result)


@router.delete("/{member_id}")
async def delete_member(member_id: str, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(member_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid member ID")
    result = await db.members.delete_one({"_id": oid, "owner_id": _owner["owner_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    # Also remove user account
    await db.users.delete_one({"_id": oid})
    return {"message": "Member deleted successfully"}
