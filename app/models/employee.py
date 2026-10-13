from datetime import date, datetime

from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    employee_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    full_name: Mapped[str] = mapped_column(String(160), index=True)
    work_email: Mapped[str] = mapped_column(String(200), unique=True)
    gender: Mapped[str] = mapped_column(String(10))
    date_of_birth: Mapped[date] = mapped_column(Date)
    hire_date: Mapped[date] = mapped_column(Date)
    exit_date: Mapped[date | None] = mapped_column(Date)
    employment_status: Mapped[str] = mapped_column(String(30), default="Active")
    employment_type: Mapped[str] = mapped_column(String(30), default="Permanent")
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id"), index=True
    )
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.role_id"))
    manager_id: Mapped[str | None] = mapped_column(
        ForeignKey("employees.employee_id"), index=True
    )
    work_location: Mapped[str] = mapped_column(String(60))
    work_mode: Mapped[str] = mapped_column(String(20))
    highest_education: Mapped[str] = mapped_column(String(100))
    prior_experience_years: Mapped[float] = mapped_column(Numeric(4, 1))
    career_gap_months: Mapped[int] = mapped_column(Integer)
    commute_distance_km: Mapped[float] = mapped_column(Numeric(5, 1))
    pf_applicable: Mapped[str] = mapped_column(String(1))
    esi_applicable: Mapped[str] = mapped_column(String(1))
    notice_period_days: Mapped[int] = mapped_column(Integer)
    resignation_date: Mapped[date | None] = mapped_column(Date)
    exit_type: Mapped[str | None] = mapped_column(String(30))
    exit_reason: Mapped[str | None] = mapped_column(String(60))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    department = relationship("Department", back_populates="employees")
    role = relationship("Role", back_populates="employees")
    manager = relationship(
        "Employee", remote_side=[employee_id], back_populates="direct_reports"
    )
    direct_reports = relationship("Employee", back_populates="manager")