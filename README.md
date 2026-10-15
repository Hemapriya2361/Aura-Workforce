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

In a second terminal, build the tables:

```
docker compose run --rm api alembic upgrade head
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

Tests use an in-memory SQLite database, so they need no Docker. They cover the models and every Task 3 endpoint, including bad input.

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
scripts/         seed script
docs/            API contract, sample data, ER diagram
```

## Handoff package

- [Draft API contract](docs/api-contract.md)
- [Sample employees (10 records)](scripts/sample_employees.json)

Tag: `handoff-day2`.