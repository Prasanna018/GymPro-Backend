from fastapi import APIRouter, HTTPException, Depends
from database import get_db
from models.plan import PlanCreate, PlanUpdate, PlanOut
from auth import require_owner, get_current_user
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/plans", tags=["Membership Plans"])


def plan_doc_to_out(doc: dict) -> PlanOut:
    return PlanOut(
        id=str(doc["_id"]),
        name=doc["name"],
        duration=doc["duration"],
        price=doc["price"],
        features=doc.get("features", []),
    )


@router.get("", response_model=List[PlanOut])
async def list_plans(_user=Depends(get_current_user)):
    db = get_db()
    plans = await db.plans.find({"owner_id": _user["owner_id"]}).sort("price", 1).to_list(100)
    return [plan_doc_to_out(p) for p in plans]


@router.post("", response_model=PlanOut, status_code=201)
async def create_plan(body: PlanCreate, _owner=Depends(require_owner)):
    db = get_db()
    doc = body.model_dump()
    doc["owner_id"] = _owner["owner_id"]
    result = await db.plans.insert_one(doc)
    doc["_id"] = result.inserted_id
    return plan_doc_to_out(doc)


@router.put("/{plan_id}", response_model=PlanOut)
async def update_plan(plan_id: str, body: PlanUpdate, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = await db.plans.find_one_and_update(
        {"_id": oid, "owner_id": _owner["owner_id"]}, {"$set": update_data}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan_doc_to_out(result)


@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(plan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    result = await db.plans.delete_one({"_id": oid, "owner_id": _owner["owner_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return {"message": "Plan deleted successfully"}
