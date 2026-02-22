from fastapi import APIRouter, HTTPException, Depends, status
from database import get_db
from models.user import UserLogin, TokenResponse, UserOut, ChangePasswordRequest, UserRegister, ForgotPasswordRequest, ResetPasswordRequest
from auth import (
    verify_password, get_password_hash, create_access_token, get_current_user
)
from bson import ObjectId
import secrets
from datetime import datetime, timedelta
from email_utils import send_reset_email

router = APIRouter(prefix="/auth", tags=["Auth"])


def user_doc_to_out(doc: dict) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        role=doc["role"],
        phone=doc.get("phone"),
        avatar=doc.get("avatar"),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: UserRegister):
    db = get_db()
    existing = await db.users.find_one({"email": body.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    user_doc = {
        "name": body.name,
        "email": body.email,
        "hashed_password": get_password_hash(body.password),
        "role": "owner",
        "phone": body.phone,
        "avatar": None
    }
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    # Also initialize dummy gym settings for this new owner
    await db.gym_settings.insert_one({
        "owner_id": str(user_doc["_id"]),
        "gym_name": f"{body.name}'s Gym",
        "owner_name": body.name,
        "email": body.email,
        "phone": body.phone or "",
        "address": "Please update your address",
        "opening_time": "06:00",
        "closing_time": "22:00",
        "notifications": {
            "email_alerts": True,
            "sms_alerts": False,
            "payment_reminders": True,
            "attendance_reports": True
        }
    })

    token = create_access_token({
        "sub": str(user_doc["_id"]),
        "email": user_doc["email"],
        "role": user_doc["role"],
        "owner_id": str(user_doc["_id"])
    })
    
    return TokenResponse(
        access_token=token,
        user=user_doc_to_out(user_doc)
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    db = get_db()
    user = await db.users.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token_payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"]
    }
    if user["role"] == "member":
        token_payload["owner_id"] = user.get("owner_id")
    else:
        token_payload["owner_id"] = str(user["_id"])

    token = create_access_token(token_payload)
    return TokenResponse(
        access_token=token,
        user=user_doc_to_out(user)
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    db = get_db()
    # Try to get from users collection first
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        # Might be a member who got a user account
        member = await db.members.find_one({"_id": ObjectId(current_user["user_id"])})
        if not member:
            raise HTTPException(status_code=404, detail="User not found")
        return UserOut(
            id=str(member["_id"]),
            name=member["name"],
            email=member["email"],
            role="member",
            phone=member.get("phone"),
        )
    return user_doc_to_out(user)


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # JWT is stateless — client should discard the token
    return {"message": "Logged out successfully"}


@router.put("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(body.current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = get_password_hash(body.new_password)
    await db.users.update_one(
        {"_id": ObjectId(current_user["user_id"])},
        {"$set": {"hashed_password": new_hash}}
    )
    return {"message": "Password updated successfully"}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    db = get_db()
    user = await db.users.find_one({"email": body.email})
    if not user or user.get("role") != "owner":
        # For security reasons, don't reveal if user exists or is an owner
        return {"message": "If this email is registered as an owner account, you will receive a reset token."}
    
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)
    
    await db.users.update_one(
        {"email": body.email},
        {"$set": {"reset_token": token, "reset_token_expiry": expiry}}
    )
    
    # Send real email using SMTP
    await send_reset_email(body.email, token)
    
    return {"message": "If this email is registered, you will receive a reset token."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    db = get_db()
    user = await db.users.find_one({
        "reset_token": body.token,
        "reset_token_expiry": {"$gt": datetime.utcnow()}
    })
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    new_hash = get_password_hash(body.password)
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": new_hash}, "$unset": {"reset_token": "", "reset_token_expiry": ""}}
    )
    
    return {"message": "Password has been reset successfully"}
