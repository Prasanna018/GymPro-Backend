# GymPro Backend 🏋️

A complete FastAPI backend for the **GymPro Gym Management System**, backed by MongoDB Atlas.

## Features

- 🔐 **JWT Authentication** — Owner & Member roles
- 👥 **Members** — Full CRUD with auto plan/expiry calculation
- 💳 **Payments** — Record & collect payments, invoice IDs
- 📅 **Attendance** — Check-in / Check-out tracking
- 🥤 **Supplement Store** — Inventory management with stock control
- 🛒 **Orders** — Member cart checkout with stock deduction
- 📊 **Dashboard & Reports** — Stats, revenue charts, membership distribution
- ⚙️ **Settings** — Gym info & notification preferences
- 🔔 **Reminders** — Identify expiring/overdue members

## Quick Start (The Easy Way)

Just double-click the `start_gympro.bat` file in the root directory!

Or run it from the terminal:
```bash
cd GymPro-Backend
..\\start_gympro.bat
```
*(This will open the backend API on port 8000 and the frontend UI on port 8080).*

### 5. Open API docs
Visit → **http://localhost:8000/docs**

---

## Default Credentials

| Role   | Email               | Password   |
|--------|---------------------|------------|
| Owner  | owner@gympro.com    | admin123   |
| Member | rahul@email.com     | member123  |
| Member | priya@email.com     | member123  |
| Member | amit@email.com      | member123  |
| Member | sneha@email.com     | member123  |
| Member | vikram@email.com    | member123  |

---

## API Endpoints Summary

| Module           | Prefix           | Key Endpoints |
|------------------|------------------|---------------|
| Auth             | `/auth`          | POST /login, GET /me, PUT /change-password |
| Members          | `/members`       | CRUD + GET/PUT /me |
| Plans            | `/plans`         | CRUD |
| Payments         | `/payments`      | List, Record, Collect |
| Attendance       | `/attendance`    | Check-in, Check-out, List |
| Supplements      | `/supplements`   | CRUD + search |
| Orders           | `/orders`        | Place, List, My Orders |
| Dashboard        | `/dashboard`     | GET /stats |
| Reports          | `/reports`       | revenue, membership, attendance |
| Settings         | `/settings`      | GET, PUT |
| Reminders        | `/reminders`     | pending, email, whatsapp |

---

## Project Structure

```
GymPro-Backend/
├── main.py           # FastAPI app, CORS, lifespan
├── database.py       # Motor MongoDB client
├── auth.py           # JWT + bcrypt utilities + role guards
├── seed.py           # Database seeder
├── requirements.txt
├── .env              # Your MongoDB URL goes here
├── models/           # Pydantic schemas
│   ├── user.py
│   ├── member.py
│   ├── plan.py
│   ├── payment.py
│   ├── attendance.py
│   ├── supplement.py
│   ├── order.py
│   └── settings.py
└── routes/           # Route handlers
    ├── auth.py
    ├── members.py
    ├── plans.py
    ├── payments.py
    ├── attendance.py
    ├── supplements.py
    ├── orders.py
    ├── dashboard.py
    ├── settings.py
    └── reminders.py
```

## Connect Frontend

In `GymPro-Frontend/.env` (create if missing):
```
VITE_API_URL=http://localhost:8000
```

Then replace mock data calls with API calls using this base URL.
