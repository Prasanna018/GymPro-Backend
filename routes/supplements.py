from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db
from models.supplement import SupplementCreate, SupplementUpdate, SupplementOut
from auth import require_owner, get_current_user
from bson import ObjectId
from typing import Optional, List

router = APIRouter(prefix="/supplements", tags=["Supplements"])


def supplement_doc_to_out(doc: dict) -> SupplementOut:
    return SupplementOut(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc["description"],
        price=doc["price"],
        stock=doc["stock"],
        category=doc["category"],
        image=doc.get("image"),
    )


@router.get("", response_model=List[SupplementOut])
async def list_supplements(
    search: Optional[str] = Query(None),
    _user=Depends(get_current_user),
):
    db = get_db()
    query = {"owner_id": _user["owner_id"]}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"category": {"$regex": search, "$options": "i"}},
        ]
    supplements = await db.supplements.find(query).sort("name", 1).to_list(500)
    return [supplement_doc_to_out(s) for s in supplements]


@router.post("", response_model=SupplementOut, status_code=201)
async def create_supplement(body: SupplementCreate, _owner=Depends(require_owner)):
    db = get_db()
    doc = body.model_dump()
    doc["owner_id"] = _owner["owner_id"]
    result = await db.supplements.insert_one(doc)
    doc["_id"] = result.inserted_id
    return supplement_doc_to_out(doc)


@router.put("/{supplement_id}", response_model=SupplementOut)
async def update_supplement(supplement_id: str, body: SupplementUpdate, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(supplement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid supplement ID")
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    result = await db.supplements.find_one_and_update(
        {"_id": oid, "owner_id": _owner["owner_id"]}, {"$set": update_data}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Supplement not found")
    return supplement_doc_to_out(result)


@router.delete("/{supplement_id}")
async def delete_supplement(supplement_id: str, _owner=Depends(require_owner)):
    db = get_db()
    try:
        oid = ObjectId(supplement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid supplement ID")
    result = await db.supplements.delete_one({"_id": oid, "owner_id": _owner["owner_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplement not found")
    return {"message": "Supplement deleted successfully"}
