from fastapi import APIRouter, Depends
from database import get_db
from auth import require_owner
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List

router = APIRouter(tags=["Dashboard & Reports"])


@router.get("/dashboard/stats")
async def dashboard_stats(_owner=Depends(require_owner)):
    db = get_db()
    today = date.today().isoformat()
    owner_id = _owner["owner_id"]

    # Auto-expire members
    await db.members.update_many(
        {"expiry_date": {"$lt": today}, "status": "active", "owner_id": owner_id},
        {"$set": {"status": "expired"}}
    )

    total_members = await db.members.count_documents({"owner_id": owner_id})
    active_members = await db.members.count_documents({"status": "active", "owner_id": owner_id})
    expired_members = await db.members.count_documents({"status": "expired", "owner_id": owner_id})

    # Revenue aggregation
    revenue_pipeline = [
        {"$match": {"status": "paid", "owner_id": owner_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await db.payments.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0

    # Pending dues: sum of all members' due_amount
    dues_pipeline = [
        {"$match": {"due_amount": {"$gt": 0}, "owner_id": owner_id}},
        {"$group": {"_id": None, "total": {"$sum": "$due_amount"}}}
    ]
    dues_result = await db.members.aggregate(dues_pipeline).to_list(1)
    pending_dues = dues_result[0]["total"] if dues_result else 0

    # Monthly revenue (current month)
    first_of_month = date.today().replace(day=1).isoformat()
    monthly_pipeline = [
        {"$match": {"status": "paid", "date": {"$gte": first_of_month}, "owner_id": owner_id}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    monthly_result = await db.payments.aggregate(monthly_pipeline).to_list(1)
    monthly_revenue = monthly_result[0]["total"] if monthly_result else 0

    return {
        "totalMembers": total_members,
        "activeMembers": active_members,
        "expiredMembers": expired_members,
        "totalRevenue": total_revenue,
        "pendingDues": pending_dues,
        "monthlyRevenue": monthly_revenue,
    }


@router.get("/reports/revenue")
async def revenue_report(_owner=Depends(require_owner)):
    db = get_db()
    months = []
    today = date.today()
    for i in range(5, -1, -1):
        first = (today.replace(day=1) - relativedelta(months=i))
        label = first.strftime("%b")
        prefix = first.strftime("%Y-%m")
        pipeline = [
            {"$match": {"status": "paid", "date": {"$regex": f"^{prefix}"}, "owner_id": _owner["owner_id"]}},
            {"$group": {"_id": None, "revenue": {"$sum": "$amount"}}}
        ]
        result = await db.payments.aggregate(pipeline).to_list(1)
        revenue = result[0]["revenue"] if result else 0
        months.append({"month": label, "revenue": revenue})
    return months


@router.get("/reports/membership")
async def membership_report(_owner=Depends(require_owner)):
    db = get_db()
    plans = await db.plans.find({"owner_id": _owner["owner_id"]}).to_list(100)
    result = []
    for plan in plans:
        count = await db.members.count_documents({"plan_id": str(plan["_id"]), "owner_id": _owner["owner_id"]})
        result.append({"name": plan["name"], "value": count})
    return result


@router.get("/reports/attendance")
async def attendance_report(_owner=Depends(require_owner)):
    db = get_db()
    # Weekly attendance: last 7 days per day of week
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    result = []
    today = date.today()
    for i in range(6, -1, -1):
        d = today - __import__("datetime").timedelta(days=i)
        count = await db.attendance.count_documents({"date": d.isoformat(), "owner_id": _owner["owner_id"]})
        result.append({"day": days[d.weekday() + 1 if d.weekday() < 6 else 0], "attendance": count})
    return result
