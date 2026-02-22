from fastapi import APIRouter, Depends
from database import get_db
from models.settings import GymSettingsUpdate, GymSettingsOut
from auth import require_owner, get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

# Default settings document key
SETTINGS_KEY = "gym_settings"


@router.get("", response_model=GymSettingsOut)
async def get_settings(current_user: dict = Depends(get_current_user)):
    db = get_db()
    owner_id = current_user["owner_id"]
    settings = await db.gym_settings.find_one({"owner_id": owner_id})
    if not settings:
        return GymSettingsOut()
    settings.pop("_id", None)
    settings.pop("owner_id", None)
    return GymSettingsOut(**settings)


@router.put("", response_model=GymSettingsOut)
async def update_settings(body: GymSettingsUpdate, _owner=Depends(require_owner)):
    db = get_db()
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}

    # Handle nested notifications dict
    if "notifications" in update_data and isinstance(update_data["notifications"], dict):
        update_data["notifications"] = update_data["notifications"]

    existing = await db.gym_settings.find_one({"owner_id": _owner["owner_id"]})
    if not existing:
        # Create default + apply updates
        default = GymSettingsOut().model_dump()
        default.update(update_data)
        default["owner_id"] = _owner["owner_id"]
        await db.gym_settings.insert_one(default)
    else:
        await db.gym_settings.update_one(
            {"owner_id": _owner["owner_id"]},
            {"$set": update_data}
        )

    settings = await db.gym_settings.find_one({"owner_id": _owner["owner_id"]})
    settings.pop("_id", None)
    settings.pop("owner_id", None)
    return GymSettingsOut(**settings)
