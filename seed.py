"""
GymPro Database Seed Script
=============================
Run this script ONCE after setting up the backend to populate:
  - 3 membership plans
  - 1 owner user (owner@gympro.com / admin123)
  - 5 sample members with user accounts (password: member123)
  - 6 supplements
  - Sample payments and attendance

Usage:
    python seed.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from dotenv import load_dotenv
from bson import ObjectId
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "gympro")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_pw(pw: str) -> str:
    return pwd_context.hash(pw)


async def seed():
    if not MONGODB_URL or MONGODB_URL == "YOUR_MONGODB_ATLAS_URL_HERE":
        print("❌  Please set MONGODB_URL in your .env file before seeding!")
        return

    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[DATABASE_NAME]

    print("🌱 Seeding GymPro database...")

    # ── Clear existing data ────────────────────────────────────────────
    await db.users.delete_many({})
    await db.members.delete_many({})
    await db.plans.delete_many({})
    await db.supplements.delete_many({})
    await db.payments.delete_many({})
    await db.attendance.delete_many({})
    await db.orders.delete_many({})
    await db.gym_settings.delete_many({})
    print("   🗑️  Cleared existing collections")

    # ── Owner User ─────────────────────────────────────────────────────
    owner_doc = {
        "name": "GymPro Admin",
        "email": "owner@gympro.com",
        "hashed_password": hash_pw("admin123"),
        "role": "owner",
        "phone": "+91 98765 43210",
        "avatar": None,
    }
    owner_result = await db.users.insert_one(owner_doc)
    owner_id_str = str(owner_result.inserted_id)
    print(f"   ✅ Owner user created (owner@gympro.com / admin123)")

    # ── Membership Plans ───────────────────────────────────────────────
    plans_data = [
        {
            "owner_id": owner_id_str,
            "name": "Monthly",
            "duration": 1,
            "price": 1500,
            "features": ["Full gym access", "Locker facility", "Basic training"],
        },
        {
            "owner_id": owner_id_str,
            "name": "Quarterly",
            "duration": 3,
            "price": 4000,
            "features": [
                "Full gym access",
                "Locker facility",
                "Personal trainer (2 sessions)",
                "Diet consultation",
            ],
        },
        {
            "owner_id": owner_id_str,
            "name": "Yearly",
            "duration": 12,
            "price": 12000,
            "features": [
                "Full gym access",
                "Premium locker",
                "Personal trainer (weekly)",
                "Diet plan",
                "Supplements discount",
            ],
        },
    ]
    plan_results = await db.plans.insert_many(plans_data)
    plan_ids = [str(pid) for pid in plan_results.inserted_ids]
    print(f"   ✅ Inserted {len(plan_ids)} plans")

    # ── Sample Members ─────────────────────────────────────────────────
    today = date.today()

    members_data = [
        {
            "owner_id": owner_id_str,
            "name": "Rahul Sharma",
            "email": "rahul@email.com",
            "phone": "+91 98765 43210",
            "address": "123 MG Road, Mumbai",
            "plan_id": plan_ids[2],  # Yearly
            "joining_date": "2024-01-15",
            "expiry_date": "2025-01-15",
            "status": "active",
            "due_amount": 0,
            "paid_amount": 12000,
            "blood_group": "O+",
            "height": 175,
            "weight": 72,
            "goal": "Muscle Building",
            "avatar": None,
        },
        {
            "owner_id": owner_id_str,
            "name": "Priya Patel",
            "email": "priya@email.com",
            "phone": "+91 87654 32109",
            "address": "456 Park Street, Delhi",
            "plan_id": plan_ids[1],  # Quarterly
            "joining_date": "2024-06-01",
            "expiry_date": (today + relativedelta(months=3)).isoformat(),
            "status": "active",
            "due_amount": 0,
            "paid_amount": 4000,
            "blood_group": "A+",
            "height": 162,
            "weight": 55,
            "goal": "Weight Loss",
            "avatar": None,
        },
        {
            "owner_id": owner_id_str,
            "name": "Amit Kumar",
            "email": "amit@email.com",
            "phone": "+91 76543 21098",
            "address": "789 Lake View, Bangalore",
            "plan_id": plan_ids[0],  # Monthly
            "joining_date": (today - relativedelta(months=1)).isoformat(),
            "expiry_date": today.isoformat(),
            "status": "active",
            "due_amount": 1500,
            "paid_amount": 0,
            "blood_group": "B+",
            "height": 180,
            "weight": 80,
            "goal": "Strength Training",
            "avatar": None,
        },
        {
            "owner_id": owner_id_str,
            "name": "Sneha Reddy",
            "email": "sneha@email.com",
            "phone": "+91 65432 10987",
            "address": "321 Hill Road, Hyderabad",
            "plan_id": plan_ids[2],  # Yearly
            "joining_date": "2024-10-15",
            "expiry_date": "2025-10-15",
            "status": "active",
            "due_amount": 0,
            "paid_amount": 12000,
            "blood_group": "AB+",
            "height": 165,
            "weight": 60,
            "goal": "Flexibility",
            "avatar": None,
        },
        {
            "owner_id": owner_id_str,
            "name": "Vikram Singh",
            "email": "vikram@email.com",
            "phone": "+91 54321 09876",
            "address": "654 Garden Lane, Pune",
            "plan_id": plan_ids[1],  # Quarterly
            "joining_date": "2024-08-01",
            "expiry_date": "2024-11-01",
            "status": "expired",
            "due_amount": 2000,
            "paid_amount": 2000,
            "blood_group": "O-",
            "height": 178,
            "weight": 85,
            "goal": "Endurance",
            "avatar": None,
        },
    ]

    for member in members_data:
        result = await db.members.insert_one(member.copy())
        member_id = result.inserted_id
        # Create login account with same _id
        await db.users.insert_one({
            "_id": member_id,
            "name": member["name"],
            "email": member["email"],
            "hashed_password": hash_pw("member123"),
            "role": "member",
            "phone": member["phone"],
            "owner_id": owner_id_str,
        })

    print(f"   ✅ Inserted {len(members_data)} members (password: member123 each)")

    # ── Supplements ────────────────────────────────────────────────────
    supplements_data = [
        {"owner_id": owner_id_str, "name": "Whey Protein Gold", "description": "Premium whey protein with 24g protein per serving", "price": 2500, "stock": 25, "category": "Protein"},
        {"owner_id": owner_id_str, "name": "BCAA Energy", "description": "Branch chain amino acids for muscle recovery", "price": 1200, "stock": 40, "category": "Amino Acids"},
        {"owner_id": owner_id_str, "name": "Pre-Workout Blast", "description": "High energy pre-workout formula", "price": 1800, "stock": 15, "category": "Pre-Workout"},
        {"owner_id": owner_id_str, "name": "Creatine Monohydrate", "description": "Pure creatine for strength and power", "price": 800, "stock": 50, "category": "Creatine"},
        {"owner_id": owner_id_str, "name": "Mass Gainer Pro", "description": "High calorie mass gainer for bulking", "price": 3200, "stock": 8, "category": "Mass Gainer"},
        {"owner_id": owner_id_str, "name": "Multivitamin Complex", "description": "Complete daily vitamin and mineral support", "price": 600, "stock": 60, "category": "Vitamins"},
    ]
    await db.supplements.insert_many(supplements_data)
    print(f"   ✅ Inserted {len(supplements_data)} supplements")

    # ── Sample Payments ─────────────────────────────────────────────────
    all_members = await db.members.find().to_list(100)
    payments_data = []
    for i, member in enumerate(all_members[:3]):
        plan = await db.plans.find_one({"_id": ObjectId(member["plan_id"])})
        payments_data.append({
            "owner_id": owner_id_str,
            "member_id": str(member["_id"]),
            "amount": member["paid_amount"],
            "date": member["joining_date"],
            "status": "paid" if member["paid_amount"] > 0 else "pending",
            "plan_id": member["plan_id"],
            "method": ["UPI", "Card", "Cash"][i % 3],
            "invoice_id": f"INV-SEED-{str(i+1).zfill(3)}",
        })
    if payments_data:
        await db.payments.insert_many(payments_data)
        print(f"   ✅ Inserted {len(payments_data)} sample payments")

    # ── Sample Attendance ───────────────────────────────────────────────
    attendance_data = []
    for i in range(5):
        d = (today - timedelta(days=i)).isoformat()
        for member in all_members[:3]:
            attendance_data.append({
                "owner_id": owner_id_str,
                "member_id": str(member["_id"]),
                "date": d,
                "check_in": f"0{6+i}:30",
                "check_out": f"0{8+i}:00",
            })
    await db.attendance.insert_many(attendance_data)
    print(f"   ✅ Inserted {len(attendance_data)} sample attendance records")

    # ── Default Gym Settings ─────────────────────────────────────────────
    await db.gym_settings.insert_one({
        "owner_id": owner_id_str,
        "gym_name": "GymPro Fitness Center",
        "owner_name": "GymPro Admin",
        "email": "owner@gympro.com",
        "phone": "+91 98765 43210",
        "address": "123 Fitness Street, Mumbai, India",
        "opening_time": "06:00",
        "closing_time": "22:00",
        "notifications": {
            "email_alerts": True,
            "sms_alerts": False,
            "payment_reminders": True,
            "attendance_reports": True,
        },
    })
    print("   ✅ Default gym settings inserted")

    client.close()
    print("\n🎉 Database seeded successfully!")
    print("\n📋 Login Credentials:")
    print("   Owner  → owner@gympro.com  / admin123")
    print("   Member → rahul@email.com   / member123")
    print("   Member → priya@email.com   / member123")
    print("   Member → amit@email.com    / member123")
    print("   Member → sneha@email.com   / member123")
    print("   Member → vikram@email.com  / member123")
    print("\n🚀 Run the server: uvicorn main:app --reload")
    print("📖 API Docs:        http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
