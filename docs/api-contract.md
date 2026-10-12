# Aura Workforce API: Draft Contract (v0.1)

Status: **draft**. Paths and fields may change in Tasks 2 and 3. Interactive docs are at `/docs` once the app is running.

## Employee object

| Field | Type | Notes |
|---|---|---|
| id | integer | |
| name | string | not empty |
| work_email | string | valid email, unique |
| department | string | e.g. Engineering, HR, Finance |
| role | string | job title |
| manager_id | integer or null | points to another employee, null for the top person |
| joining_date | date (YYYY-MM-DD) | cannot be in the future |
| phone | string | |
| is_active | boolean | false after a soft delete |

## Endpoints

| Method | Path | Purpose | Request | Success response |
|---|---|---|---|---|
| GET | /health | Service check | none | 200 `{"status": "ok"}` |
| POST | /employees | Create an employee | name, work_email, department, role, manager_id, joining_date, phone | 201 employee |
| GET | /employees | List employees | query: page, size, department, q | 200 `{items, total, page, size}` |
| GET | /employees/{id} | Get one employee | none | 200 employee |
| PATCH | /employees/{id} | Update some fields | any employee fields | 200 employee |
| DELETE | /employees/{id} | Soft delete (is_active = false) | none | 204 |
| GET | /employees/{id}/team | Direct reports of an employee | none | 200 list of employees |
| GET | /departments | List departments | none | 200 list |
| GET | /departments/{id}/employees | Employees in a department | none | 200 list of employees |

## List query parameters

`GET /employees?page=1&size=20&department=Marketing&q=sample2`

- `page` starts at 1, `size` defaults to 20
- `department` filters by department name
- `q` searches by name
- the response always includes `total` so screens can build pagination

## Error format

Every error uses the same shape:

```json
{"detail": "Employee not found"}
```

| Status | When |
|---|---|
| 400 / 422 | bad input (invalid email, empty name, future joining date) |
| 404 | id does not exist |
| 409 | duplicate work email |

## Sample data

See `sample_employees.json` (10 fake employees).
