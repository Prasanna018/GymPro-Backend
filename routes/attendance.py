from fastapi import APIRouter, HTTPException, Depends, Query
from database import get_db
from models.attendance import AttendanceCreate, AttendanceCheckout, AttendanceOut
from auth import require_owner, get_current_user
from bson import ObjectId
from datetime import date, datetime
from typing import Optional, List

router = APIRouter(prefix="/attendance", tags=["Attendance"])


def attendance_doc_to_out(doc: dict) -> AttendanceOut:
    return AttendanceOut(
        id=str(doc["_id"]),
        member_id=doc["member_id"],
        date=doc["date"],
        check_in=doc["check_in"],
        check_out=doc.get("check_out"),
    )


@router.get("", response_model=List[AttendanceOut])
async def list_attendance(
    date_filter: Optional[str] = Query(None, alias="date"),
    member_id: Optional[str] = Query(None),
    _owner=Depends(require_owner),
):
    db = get_db()
    query = {"owner_id": _owner["owner_id"]}
    if date_filter:
        query["date"] = date_filter
    if member_id:
        query["member_id"] = member_id
    records = await db.attendance.find(query).sort("date", -1).to_list(1000)
    return [attendance_doc_to_out(r) for r in records]


@router.get("/me", response_model=List[AttendanceOut])
async def my_attendance(
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    member = await db.members.find_one({"email": current_user["email"]})
    if not member:
        raise HTTPException(status_code=404, detail="Member profile not found")
    member_id = str(member["_id"])
    query: dict = {"member_id": member_id}
    if month and year:
        prefix = f"{year}-{str(month).zfill(2)}"
        query["date"] = {"$regex": f"^{prefix}"}
    records = await db.attendance.find(query).sort("date", -1).to_list(200)
    return [attendance_doc_to_out(r) for r in records]


@router.post("/checkin", response_model=AttendanceOut, status_code=201)
async def check_in(body: AttendanceCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    today = date.today().isoformat()
    now_time = datetime.now().strftime("%H:%M")

    if current_user["role"] == "owner":
        # Owner can check in any member by member_id
        if not body.member_id:
            raise HTTPException(status_code=400, detail="member_id required for owner check-in")
        try:
            mid = ObjectId(body.member_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid member_id")
        member = await db.members.find_one({"_id": mid, "owner_id": current_user["owner_id"]})
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        member_id = body.member_id
        target_date = body.date or today
        check_in_time = body.check_in or now_time
    else:
        # Member checks themselves in
        member = await db.members.find_one({"email": current_user["email"]})
        if not member:
            raise HTTPException(status_code=404, detail="Member profile not found")
        member_id = str(member["_id"])
        target_date = today
        check_in_time = now_time

    # Check if already checked in today
    existing = await db.attendance.find_one({"member_id": member_id, "date": target_date, "owner_id": current_user["owner_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Member already checked in for this date")

    doc = {
        "owner_id": current_user["owner_id"],
        "member_id": member_id,
        "date": target_date,
        "check_in": check_in_time,
        "check_out": None,
    }
    result = await db.attendance.insert_one(doc)
    doc["_id"] = result.inserted_id
    return attendance_doc_to_out(doc)


@router.put("/{attendance_id}/checkout", response_model=AttendanceOut)
async def check_out(
    attendance_id: str,
    body: AttendanceCheckout,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    try:
        oid = ObjectId(attendance_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid attendance ID")

    now_time = datetime.now().strftime("%H:%M")
    checkout_time = body.check_out or now_time

    result = await db.attendance.find_one_and_update(
        {"_id": oid, "check_out": None, "owner_id": current_user["owner_id"]},
        {"$set": {"check_out": checkout_time}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Attendance record not found or already checked out")
    return attendance_doc_to_out(result)
