from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from database import connect_db, close_db

# Import all routers
from routes.auth import router as auth_router
from routes.members import router as members_router
from routes.plans import router as plans_router
from routes.payments import router as payments_router
from routes.attendance import router as attendance_router
from routes.supplements import router as supplements_router
from routes.orders import router as orders_router
from routes.dashboard import router as dashboard_router
from routes.settings import router as settings_router
from routes.reminders import router as reminders_router
from routes.razorpay_payments import router as razorpay_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(
    title="GymPro API",
    description="Complete backend for GymPro Gym Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8080")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(auth_router)
app.include_router(members_router)
app.include_router(plans_router)
app.include_router(payments_router)
app.include_router(attendance_router)
app.include_router(supplements_router)
app.include_router(orders_router)
app.include_router(dashboard_router)
app.include_router(settings_router)
app.include_router(reminders_router)
app.include_router(razorpay_router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "GymPro API is running 🏋️",
        "docs": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
