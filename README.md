# SahaTakvim

Production-oriented Flask web app for halı saha reservation, weekly calendar operations, day-end closing, finance tracking, and monthly forecasting.

## Architecture (Step 1)
- **App factory** pattern (`app/__init__.py`)
- Modular blueprints: `auth`, `main`, `calendar`, `fields`, `finance`, `reports`
- ORM with SQLAlchemy models for users, fields, reservations, closings, incomes, expenses, settings
- Role-based access with `admin` and `employee`
- Weekly calendar with business-first rule: **00:00–02:00 belongs to selected day evening session**
- Render-ready with `gunicorn`, PostgreSQL compatibility, and `render.yaml`

## Project Structure (Step 2)
```text
/app
  /auth /main /calendar /fields /finance /reports
  /templates /static
  __init__.py config.py extensions.py models.py
/migrations
/instance
.env.example
requirements.txt
run.py
render.yaml
README.md
```

## Backend Setup (Steps 3-5)
### Local setup (without Docker)
1. Create venv
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Configure env
   ```bash
   cp .env.example .env
   ```
4. Initialize DB and migrate
   ```bash
   flask db init
   flask db migrate -m "initial"
   flask db upgrade
   ```
5. Seed admin + starter field
   ```bash
   flask seed-admin
   ```
6. Run
   ```bash
   flask run
   ```

## Models & Migration Plan (Step 4)
Core models:
- `User` (`role`: admin/employee)
- `Field` (pricing + operating hours + active flag)
- `Reservation` (type, deposit status, slot uniqueness)
- `DailyClosing` (card/cash/iban + unique date)
- `Income`, `Expense`, category tables (recurring support)
- `Setting` (business configuration)

## Weekly Calendar & Reservation Flow (Step 6)
- Monday-start weekly view
- Slot range 17:00 → 02:00
- Modal-driven reservation creation
- Type badge (`abone` / `tek_saatlik`)
- Deposit status indicators
- Edit and cancellation flow
- Double booking prevention via unique constraint + route validation

## Field Management (Step 7)
Admin can:
- Create/edit fields
- Activate/deactivate fields
- Set rental/subscription prices
- Set open/close hour per field

## Day-end Closing (Step 8)
Employee/Admin can:
- Enter card/cash/IBAN totals
- Save once per date (upsert behavior for safe revision)
- Track who entered records

## Finance Module (Step 9)
Admin can:
- Create other incomes and expenses
- Mark recurring records (monthly/yearly)
- View forecast screen
- Forecast includes recurring entries + reservation-based expected income

## Dashboards & Reports (Step 10)
- **Admin dashboard** with KPI cards and upcoming reservations
- **Employee dashboard** with today list + shortcuts
- Reservation report list for filtering-ready management

## Render Deployment (Step 11)
### Required environment variables
- `SECRET_KEY`
- `DATABASE_URL` (Render PostgreSQL URL)
- `FLASK_ENV=production`

### Start command
```bash
gunicorn run:app
```

### Build command (recommended)
```bash
pip install -r requirements.txt && flask db upgrade
```

## Docker-ready Notes (future)
The codebase is already container-friendly due to:
- app factory structure
- env-driven config
- production WSGI server (gunicorn)
- externalized DB URL

Minimal future additions:
- `Dockerfile`
- `docker-compose.yml`
- optional Nginx reverse proxy

## GitHub Commit Guidance by Steps
After each major step commit:
1. Architecture + skeleton
2. Backend + models + forms + routes
3. Templates + static polish
4. Docs + deploy files

## Troubleshooting
- If you get `sqlite3.OperationalError: unable to open database file`, ensure the app has write permission to the project folder and use an absolute SQLite path or keep `DATABASE_URL` empty so default `instance/app.db` is created automatically.
- If you see `ImportError: cannot import name 'calendar_bp' from app.calendar.routes`, pull the latest code. The app now loads the calendar blueprint defensively and also exposes a fallback alias (`bp`) in `app/calendar/routes.py`.
- If you see `ModuleNotFoundError: No module named 'app.models'`, verify that your project root contains `app/models.py` and that you are running commands from the repository root (same folder as `run.py`).
- Also ensure installation is complete with `pip install -r requirements.txt` in the active virtual environment.
