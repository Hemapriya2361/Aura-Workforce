from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Department
from app.services import employee_service
from app.services.pagination import build_page


def get_department(db: Session, department_id: str) -> Department:
    department = db.get(Department, department_id)
    if department is None:
        raise AppError(404, "NOT_FOUND", f"Department {department_id} not found")
    return department


def list_departments(db: Session, page: int, size: int) -> dict:
    total = db.scalar(select(func.count()).select_from(Department))
    stmt = (
        select(Department)
        .order_by(Department.department_id)
        .offset((page - 1) * size)
        .limit(size)
    )
    return build_page(list(db.scalars(stmt)), total, page, size)


def list_department_employees(
    db: Session, department_id: str, page: int, size: int
) -> dict:
    get_department(db, department_id)  # 404 if the department does not exist
    return employee_service.list_employees(
        db, page=page, size=size, department_id=department_id
    )