# Aura Workforce API: Draft Contract (v0.1)

Status: **draft**. Field names, ids and formats follow the shared LedgerForge Python Master Dataset. Paths and fields may still change in Tasks 2 and 3. Interactive docs are at `/docs` once the app is running.

## Conventions

- Ids are text codes: employees `EMP-0001`, departments `D01`, roles `R001`
- Dates are ISO `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS`
- Missing values are `null`

## Employee object

| Field | Type | Notes |
|---|---|---|
| employee_id | string | `EMP-0001` style, unique |
| first_name | string | not empty |
| last_name | string | not empty |
| full_name | string | first and last name |
| work_email | string | valid email, unique |
| gender | string | Male, Female or Other |
| date_of_birth | date | |
| hire_date | date | cannot be in the future |
| exit_date | date or null | last working day, null for active |
| employment_status | string | Active, Resigned, Terminated, Contract Ended |
| employment_type | string | Permanent or Fixed-Term Contract |
| department_id | string | points to a department, e.g. `D01` |
| role_id | string | points to a role, e.g. `R002` |
| manager_id | string or null | `employee_id` of the manager, null for the top person |
| work_location | string | city |
| work_mode | string | Onsite, Hybrid or Remote |
| highest_education | string or null | |
| prior_experience_years | number | |
| career_gap_months | integer | |
| commute_distance_km | number | |
| pf_applicable | string | `Y` or `N` |
| esi_applicable | string | `Y` or `N` |
| notice_period_days | integer | 30, 60 or 90 |
| resignation_date | date or null | voluntary leavers only |
| exit_type | string or null | Voluntary, Involuntary, Contract End |
| exit_reason | string or null | |
| created_at | timestamp | |

API-only field: `is_active` (boolean) is derived from `employment_status`. It is `true` only when the status is Active. A soft delete sets the employee inactive instead of removing the row.

## Department object

| Field | Type | Notes |
|---|---|---|
| department_id | string | `D00` to `D10` |
| department_name | string | e.g. Engineering |
| cost_center | string | e.g. `CC-100` |
| description | string | |

## Endpoints

| Method | Path | Purpose | Request | Success response |
|---|---|---|---|---|
| GET | /health | Service check | none | 200 `{"status": "ok"}` |
| POST | /employees | Create an employee | employee fields (no `employee_id`, `created_at` or `full_name`) | 201 employee |
| GET | /employees | List employees | query: page, size, department, q | 200 `{items, total, page, size}` |
| GET | /employees/{employee_id} | Get one employee | none | 200 employee |
| PATCH | /employees/{employee_id} | Update some fields | any editable employee fields | 200 employee |
| DELETE | /employees/{employee_id} | Soft delete (inactive) | none | 204 |
| GET | /employees/{employee_id}/team | Direct reports (employees whose `manager_id` is this id) | none | 200 list of employees |
| GET | /departments | List departments | none | 200 list of departments |
| GET | /departments/{department_id}/employees | Employees in a department | none | 200 list of employees |

## List query parameters

`GET /employees?page=1&size=20&department=D01&q=ganesh`

- `page` starts at 1, `size` defaults to 20
- `department` filters by `department_id`
- `q` searches by name
- the response always includes `total` so screens can build pagination

## Error format

Every error uses the same shape:

```json
{"detail": "Employee not found"}
```

| Status | When |
|---|---|
| 400 / 422 | bad input (invalid email, empty name, future hire date) |
| 404 | id does not exist |
| 409 | duplicate work email |

## Sample data

- `sample_employees.json`: first 10 rows of the `employees` sheet
- `sample_departments.json`: all 11 rows of the `departments` sheet

Source: LedgerForge Python Master Dataset.
