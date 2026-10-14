from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import Page
from app.schemas.department import DepartmentOut
from app.schemas.employee import EmployeeOut
from app.services import department_service

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=Page[DepartmentOut])
def list_departments(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return department_service.list_departments(db, page, size)


@router.get("/{department_id}", response_model=DepartmentOut)
def get_department(department_id: str, db: Session = Depends(get_db)):
    return department_service.get_department(db, department_id)


@router.get("/{department_id}/employees", response_model=Page[EmployeeOut])
def list_department_employees(
    department_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return department_service.list_department_employees(db, department_id, page, size)