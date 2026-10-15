from datetime import date

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Department, Employee, Role
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.pagination import build_page

SORTABLE_FIELDS = {
    "employee_id",
    "full_name",
    "work_email",
    "hire_date",
    "department_id",
    "work_location",
}

# fields that may be omitted in a PATCH but can never be set to null
NOT_NULLABLE = {
    "first_name", "last_name", "work_email", "gender", "date_of_birth",
    "hire_date", "employment_status", "employment_type", "department_id",
    "role_id", "work_location", "work_mode", "highest_education",
    "prior_experience_years", "career_gap_months", "commute_distance_km",
    "pf_applicable", "esi_applicable", "notice_period_days",
}


def _validation_error(field: str, issue: str) -> AppError:
    return AppError(
        422, "VALIDATION_ERROR", "Validation failed",
        [{"field": field, "issue": issue}],
    )


def get_employee(db: Session, employee_id: str) -> Employee:
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise AppError(404, "NOT_FOUND", f"Employee {employee_id} not found")
    return employee


def _next_employee_id(db: Session) -> str:
    last = db.scalar(select(func.max(Employee.employee_id)))
    number = int(last.split("-")[1]) + 1 if last else 1
    return f"EMP-{number:04d}"


def _email_taken(db: Session, email: str, exclude_id: str | None = None) -> bool:
    stmt = select(Employee.employee_id).where(Employee.work_email == email)
    if exclude_id:
        stmt = stmt.where(Employee.employee_id != exclude_id)
    return db.scalar(stmt) is not None


def _check_references(
    db: Session,
    department_id: str | None,
    role_id: str | None,
    manager_id: str | None,
    employee_id: str | None = None,
) -> None:
    if department_id is not None and db.get(Department, department_id) is None:
        raise _validation_error("department_id", "unknown department")
    if role_id is not None and db.get(Role, role_id) is None:
        raise _validation_error("role_id", "unknown role")
    if manager_id is not None:
        if manager_id == employee_id:
            raise _validation_error("manager_id", "an employee cannot be their own manager")
        if db.get(Employee, manager_id) is None:
            raise _validation_error("manager_id", "unknown manager")


def _save(db: Session, employee: Employee) -> Employee:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "CONFLICT", "Employee conflicts with existing data")
    db.refresh(employee)
    return employee


def create_employee(db: Session, data: EmployeeCreate) -> Employee:
    if _email_taken(db, data.work_email):
        raise AppError(409, "CONFLICT", "Work email already exists")
    _check_references(db, data.department_id, data.role_id, data.manager_id)

    employee = Employee(
        **data.model_dump(),
        employee_id=_next_employee_id(db),
        full_name=f"{data.first_name} {data.last_name}",
        employment_status="Active",
        is_active=True,
    )
    db.add(employee)
    return _save(db, employee)


def update_employee(db: Session, employee_id: str, data: EmployeeUpdate) -> Employee:
    employee = get_employee(db, employee_id)
    changes = data.model_dump(exclude_unset=True)

    for field in NOT_NULLABLE:
        if field in changes and changes[field] is None:
            raise _validation_error(field, "cannot be null")

    if "work_email" in changes and _email_taken(db, changes["work_email"], employee_id):
        raise AppError(409, "CONFLICT", "Work email already exists")
    _check_references(
        db,
        changes.get("department_id"),
        changes.get("role_id"),
        changes.get("manager_id"),
        employee_id,
    )

    hire_date = changes.get("hire_date", employee.hire_date)
    exit_date = changes.get("exit_date", employee.exit_date)
    if exit_date is not None and exit_date < hire_date:
        raise _validation_error("exit_date", "must not be before hire_date")

    for field, value in changes.items():
        setattr(employee, field, value)
    if "first_name" in changes or "last_name" in changes:
        employee.full_name = f"{employee.first_name} {employee.last_name}"
    if "employment_status" in changes:
        employee.is_active = employee.employment_status == "Active"
    return _save(db, employee)


def soft_delete_employee(db: Session, employee_id: str) -> None:
    employee = get_employee(db, employee_id)
    employee.is_active = False  # the row and its history stay
    _save(db, employee)


def list_employees(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    sort: str = "employee_id",
    department_id: str | None = None,
    role_id: str | None = None,
    employment_status: str | None = None,
    work_location: str | None = None,
    work_mode: str | None = None,
    manager_id: str | None = None,
    hire_date_from: date | None = None,
    hire_date_to: date | None = None,
    q: str | None = None,
    is_active: bool | None = None,
) -> dict:
    sort_field = sort.lstrip("-")
    if sort_field not in SORTABLE_FIELDS:
        raise _validation_error("sort", f"must be one of: {', '.join(sorted(SORTABLE_FIELDS))}")

    stmt = select(Employee)
    exact_filters = {
        Employee.department_id: department_id,
        Employee.role_id: role_id,
        Employee.employment_status: employment_status,
        Employee.work_location: work_location,
        Employee.work_mode: work_mode,
        Employee.manager_id: manager_id,
        Employee.is_active: is_active,
    }
    for column, value in exact_filters.items():
        if value is not None:
            stmt = stmt.where(column == value)
    if hire_date_from is not None:
        stmt = stmt.where(Employee.hire_date >= hire_date_from)
    if hire_date_to is not None:
        stmt = stmt.where(Employee.hire_date <= hire_date_to)
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Employee.full_name.ilike(pattern), Employee.work_email.ilike(pattern))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    direction = desc if sort.startswith("-") else asc
    stmt = (
        stmt.order_by(direction(getattr(Employee, sort_field)), Employee.employee_id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return build_page(list(db.scalars(stmt)), total, page, size)


def list_team(db: Session, employee_id: str, page: int, size: int) -> dict:
    get_employee(db, employee_id)  # 404 if the manager does not exist
    return list_employees(db, page=page, size=size, manager_id=employee_id)