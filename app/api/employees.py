from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Page
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate
from app.services import employee_service

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=Page[EmployeeOut])
def list_employees(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
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
    db: Session = Depends(get_db),
):
    return employee_service.list_employees(
        db,
        page=page,
        size=size,
        sort=sort,
        department_id=department_id,
        role_id=role_id,
        employment_status=employment_status,
        work_location=work_location,
        work_mode=work_mode,
        manager_id=manager_id,
        hire_date_from=hire_date_from,
        hire_date_to=hire_date_to,
        q=q,
        is_active=is_active,
    )


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db)):
    return employee_service.create_employee(db, data)


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    return employee_service.get_employee(db, employee_id)


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: str, data: EmployeeUpdate, db: Session = Depends(get_db)
):
    return employee_service.update_employee(db, employee_id, data)


@router.delete("/{employee_id}", status_code=204)
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    employee_service.soft_delete_employee(db, employee_id)
    return Response(status_code=204)


@router.get("/{employee_id}/team", response_model=Page[EmployeeOut])
def get_team(
    employee_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return employee_service.list_team(db, employee_id, page, size)