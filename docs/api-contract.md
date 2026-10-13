# API Contract v1 (Draft)

Base path: `/api/v1`. Every endpoint needs a login except `/health` and `/auth/login`.
Response field names follow the column names of the workbook sheets.
Ids are text codes (EMP-0001, D01, R001). Dates are ISO (YYYY-MM-DD).

## Conventions

- **Errors:** `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": [{"field": "email", "issue": "invalid format"}], "request_id": "..."}}`
  Codes: VALIDATION_ERROR 422, UNAUTHENTICATED 401, FORBIDDEN 403, NOT_FOUND 404, CONFLICT 409, INTERNAL_ERROR 500.
- **Pagination:** `page` (from 1) and `size` (default 20, max 100).
  Response: `{"items": [...], "total": 441, "page": 1, "size": 20, "pages": 23}`
- **Filters:** plain query names (`department_id=D01`), `q` for name or email search, `from` and `to` for dates, `sort=field` or `sort=-field`.
- **Money** in JSON is a string with 2 decimals (`"54788660.03"`).
- **Deleting an employee** sets `is_active = false`; history stays.
- **Login:** `POST /auth/login` with `{"username", "password"}` returns `{"access_token", "refresh_token", "token_type": "bearer", "expires_in": 900}`.

## Roles

| Resource | ADMIN | HR | EMPLOYEE |
|---|---|---|---|
| Employees | all | all (cannot change roles or users) | read own record |
| Users and roles | all | none | none |
| Salary structures and revisions | all | read and write | read own |
| Attendance | all | all | read own; mark own check-in |
| Leave requests | all, may approve any | all, may approve any | create own; a manager approves direct reports |
| Payroll runs and adjustments | create, view, approve | create, view (no approve) | none |
| Payslips | all | all | own only |
| Ledger, expenses, invoices, reports | all | none | none |
| Tax slabs | read and write | read | none |
| Compliance reports | all | all | none |
| Exports | all | people and compliance exports | none |

## Endpoints

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me` |
| Employees | `GET /employees`, `POST /employees`, `GET /employees/me`, `GET /employees/{id}`, `PATCH /employees/{id}`, `DELETE /employees/{id}`, `GET /employees/{id}/team`, `GET /employees/{id}/assignments` |
| Organisation | `GET /departments`, `GET /departments/{id}`, `GET /departments/{id}/employees`, `GET /roles` |
| Users (admin) | `GET /users`, `POST /users`, `PATCH /users/{id}` |
| Salary | `GET /salary/components`, `GET /employees/{id}/salary`, `GET /employees/{id}/salary/history`, `POST /employees/{id}/salary/revisions` |
| Attendance | `GET /attendance`, `POST /attendance`, `GET /attendance/summary?employee=me&month=2026-09` |
| Leave | `GET /leave/types`, `GET /leave/balance?employee=me`, `GET /leave/requests`, `POST /leave/requests`, `POST /leave/requests/{id}/approve`, `.../reject`, `.../cancel`, `GET /holidays` |
| Payroll | `POST /payroll/calculate`, `POST /payroll/runs`, `GET /payroll/runs`, `GET /payroll/runs/{id}`, `GET /payroll/runs/{id}/items`, `POST /payroll/runs/{id}/approve`, `GET /payroll/adjustments`, `POST /payroll/adjustments` |
| Payslips | `GET /payslips/{employee_id}/{month}`, `GET /payslips/{employee_id}/{month}/pdf`, `POST /payslips/batch` |
| Accounting | `GET /accounting/accounts`, `GET /accounting/accounts/{code}/balance?as_of=`, `GET /accounting/journal-entries`, `POST /accounting/journal-entries`, `GET /accounting/journal-entries/{id}`, `POST /accounting/journal-entries/{id}/reverse` |
| Business | `GET/POST /clients`, `GET/POST /vendors`, `GET/POST /expenses`, `POST /expenses/{id}/pay`, `GET/POST /invoices`, `GET /invoices/{id}`, `POST /invoices/{id}/send`, `POST /invoices/{id}/payments` |
| Reports | `GET /reports/trial-balance?as_of=`, `GET /reports/profit-and-loss?from=&to=`, `GET /reports/balance-sheet?as_of=`, `GET /reports/payroll-ledger-reconciliation?month=` |
| Tax and compliance | `GET/POST /tax/slabs`, `PUT /tax/slabs/{id}`, `GET /tax/calculate?annual=`, `GET /compliance/pf?month=`, `GET /compliance/esi?month=`, `GET /compliance/tds?month=` |
| Exports | `GET /exports/{dataset}?format=csv\|xlsx&updated_since=` |
| Jobs and health | `GET /jobs/{job_id}`, `GET /health` |

## Employee list filters

`GET /employees?page=1&size=20&department_id=D01&role_id=R002&employment_status=Active&work_location=Pune&work_mode=Hybrid&manager_id=EMP-0002&hire_date_from=2020-01-01&hire_date_to=2025-12-31&q=ganesh`

## Job pattern

A long operation returns `202` with `{"job_id": "...", "status_url": "/api/v1/jobs/..."}`.
`GET /jobs/{id}` returns `{"status": "pending|running|success|failed", "progress": {"done": 40, "total": 100}, "result": ..., "error": ...}`.

## Added by this team

None yet.

## Sample data

`scripts/sample_employees.json` holds 10 employees, with field names as in the employees sheet.