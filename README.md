# Aura Workforce API

Backend for an HR management system, built with FastAPI and PostgreSQL.

## What you need

- Python 3.12
- Git
- Docker (with Docker Compose)

## Run with Docker

```
git clone https://github.com/Hemapriya2361/Aura-Workforce.git
cd Aura-Workforce
copy .env.example .env        # on Mac/Linux: cp .env.example .env
docker compose up --build
```

In a second terminal, build the tables and fill them with the master dataset:

```
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m scripts.seed --reset
```

Then open:

- http://localhost:8000/api/v1/health returns `{"status": "ok"}`
- http://localhost:8000/docs shows the interactive API page

Stop with `Ctrl+C`, and `docker compose down` to remove the containers.

## Run without Docker (for quick checks)

```
python -m venv venv
venv\Scripts\activate         # on Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run the tests

```
python -m pytest
```

Tests use an in-memory SQLite database, so they need no Docker. They cover the models, every Task 3 endpoint (including bad input) and the Task 4 seed and CSV export.

## Database (Task 2)

Tables: `departments`, `roles`, `employees`. Models are in `app/models/`, and field names follow the master dataset.

![ER diagram](docs/er-diagram.png)

The diagram source is in `docs/er-diagram.dbml`.

**One role or many per employee?** One. Each employee has a single `role_id`, as in the master dataset. A single role means a single pay band, so payroll and reports stay simple. A role history table can be added later if changes over time are needed.

**Other design points**
- `manager_id` points back to `employees.employee_id`, which gives the manager and team hierarchy.
- `work_email` is unique. `full_name`, `department_id` and `manager_id` are indexed for search.
- Soft delete: `is_active` is set to false instead of deleting the row.
- `created_at` and `updated_at` are filled automatically.

### Migrations

Run these inside Docker, because the database host is `db`:

```
docker compose up -d db
docker compose run --rm api alembic upgrade head      # build the schema
docker compose run --rm api alembic downgrade base    # roll everything back
docker compose run --rm api alembic revision --autogenerate -m "message"   # new migration
```

To start from a completely clean database: `docker compose down -v`, then run the upgrade again.

## Endpoints (Task 3)

All paths start with `/api/v1`. The full list is in [docs/api-contract.md](docs/api-contract.md).

| Method | Path | What it does |
|---|---|---|
| GET | `/employees` | List with filters, search, sort and pagination |
| POST | `/employees` | Create an employee (201) |
| GET | `/employees/{id}` | One employee |
| PATCH | `/employees/{id}` | Change only the fields sent |
| DELETE | `/employees/{id}` | Soft delete, sets `is_active=false` (204) |
| GET | `/employees/{id}/team` | Direct reports of a manager |
| GET | `/departments` | List departments |
| GET | `/departments/{id}` | One department |
| GET | `/departments/{id}/employees` | Employees in a department |

**List filters:** `department_id`, `role_id`, `employment_status`, `work_location`, `work_mode`, `manager_id`, `hire_date_from`, `hire_date_to`, `is_active`, and `q` (searches name and email).
**Sorting:** `sort=hire_date` (ascending) or `sort=-hire_date` (descending).
**Pagination:** `page` (from 1) and `size` (default 20, max 100). Lists return `{items, total, page, size, pages}`.

**Errors** all use one shape:

```json
{"error": {"code": "NOT_FOUND", "message": "...", "details": [], "request_id": "..."}}
```

Codes: `VALIDATION_ERROR` (422), `NOT_FOUND` (404), `CONFLICT` (409), `INTERNAL_ERROR` (500). Stack traces are never shown.

## Master dataset and seed (Task 4)

**Data source:** `data/seed/01_LedgerForge_Python_Master_Dataset.xlsx`. Everything in it is fictional (company "Zenith Nova Technologies"). No Kaggle dataset is used.

```
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m scripts.seed --reset     # fills the database
docker compose run --rm api python -m scripts.export_csv       # CSV files in exports/
```

How the seed works:
- `--reset` empties all tables first, then loads. Without it, the seed only adds rows that are missing, so running it twice never creates duplicates.
- Employees are inserted in two passes. A manager can appear later in the sheet than the person who reports to them, so everyone is inserted first and `manager_id` is filled in second.
- The Excel file is slow to read, so each sheet is converted to CSV once (`scripts/export_sheets.py`) into `data/seed/csv/`, which is not committed.
- After loading, the seed prints a row-count table and checks (managers exist, no exit before hire, exit date matches status, 441 active, no placeholder data). It exits with an error if a check fails.
- `--with-extra` adds 50 more employees made with Faker (`scripts/extra_fake.py`, fixed seed 2026, so everyone gets the same people). They are optional so that row counts equal the sheet.

Row counts after `python -m scripts.seed --reset`:

| Table | Sheet rows | Database rows |
|---|---|---|
| departments | 11 | 11 |
| roles | 58 | 58 |
| employees | 745 (441 active) | 745 (441 active) |

**CSV exports** (`exports/`, one file per table): `employees.csv` (from the database), `salary_structures.csv` and `attendance.csv` (copied from the master dataset until Tasks 6 and 7 add those tables).

## Settings

Settings are read from environment variables, or from a `.env` file. `.env` is not committed. Copy `.env.example` and change the values.

Inside Docker the database host is the service name `db`, not `localhost`.

`DEMO_TODAY` (default `2026-09-30`) is the date the app treats as "today" for validation.

## Assumptions

- There is no login yet. Task 5 adds role checks to every endpoint.
- `employee_id` is generated as the next `EMP-nnnn`. `full_name` is built from first and last name. New employees start as Active.
- Emails are saved in lowercase.
- The employee list returns everyone by default. Use `is_active=true` for current staff.
- A role is not checked against the employee's department.
- Hire date cannot be after `DEMO_TODAY`.
- Changing `employment_status` also updates `is_active` (Active means true, anything else false).
- `/roles` endpoints are not built yet.
- The seed loads only departments, roles and employees for now. Other tables get their loaders in the task that creates them.
- The 50 Faker employees are optional (`--with-extra`), so that seeded row counts equal the sheet row counts.
- The employees table has no phone column, so no phone numbers are generated.
- `salary_structures.csv` and `attendance.csv` come from the master dataset until their tables exist.

## Folder structure

```
app/
  main.py        app entry point and /api/v1/health
  api/           API endpoints (employees, departments)
  core/          settings, database connection, error handling
  services/      business logic
  models/        database tables
  schemas/       request and response shapes
alembic/         database migrations
tests/           pytest tests
scripts/         seed.py, extra_fake.py, export_sheets.py, export_csv.py
data/seed/       master dataset workbook (csv/ is generated, not committed)
exports/         CSV exports (generated, not committed)
docs/            API contract, sample data, ER diagram
```

## Handoff package

- [Draft API contract](docs/api-contract.md)
- [Sample employees (10 records)](scripts/sample_employees.json)

- [Master dataset workbook](data/seed/01_LedgerForge_Python_Master_Dataset.xlsx)

Tag: `handoff-day2`.