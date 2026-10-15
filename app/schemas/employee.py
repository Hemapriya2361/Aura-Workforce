import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

Gender = Literal["Male", "Female", "Other"]
EmploymentType = Literal["Permanent", "Fixed-Term Contract"]
EmploymentStatus = Literal["Active", "Resigned", "Terminated", "Contract Ended"]
WorkMode = Literal["Onsite", "Hybrid", "Remote"]
YesNo = Literal["Y", "N"]


def clean_name(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be empty")
    return value


def clean_email(value: str) -> str:
    value = value.strip().lower()
    if not EMAIL_PATTERN.match(value):
        raise ValueError("invalid email format")
    return value


def check_hire_date(value: date) -> date:
    if value > settings.demo_today:
        raise ValueError(f"must not be after {settings.demo_today}")
    return value


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    work_email: str
    gender: Gender
    date_of_birth: date
    hire_date: date
    employment_type: EmploymentType = "Permanent"
    department_id: str
    role_id: str
    manager_id: str | None = None
    work_location: str
    work_mode: WorkMode
    highest_education: str
    prior_experience_years: float = Field(default=0, ge=0)
    career_gap_months: int = Field(default=0, ge=0)
    commute_distance_km: float = Field(ge=0)
    pf_applicable: YesNo = "Y"
    esi_applicable: YesNo = "N"
    notice_period_days: int = Field(default=30, ge=0)

    @field_validator("first_name", "last_name")
    @classmethod
    def _name(cls, value):
        return clean_name(value)

    @field_validator("work_email")
    @classmethod
    def _email(cls, value):
        return clean_email(value)

    @field_validator("hire_date")
    @classmethod
    def _hire_date(cls, value):
        return check_hire_date(value)


class EmployeeUpdate(BaseModel):
    """Every field is optional. Only the fields that are sent get changed."""

    first_name: str | None = None
    last_name: str | None = None
    work_email: str | None = None
    gender: Gender | None = None
    date_of_birth: date | None = None
    hire_date: date | None = None
    employment_status: EmploymentStatus | None = None
    employment_type: EmploymentType | None = None
    department_id: str | None = None
    role_id: str | None = None
    manager_id: str | None = None
    work_location: str | None = None
    work_mode: WorkMode | None = None
    highest_education: str | None = None
    prior_experience_years: float | None = Field(default=None, ge=0)
    career_gap_months: int | None = Field(default=None, ge=0)
    commute_distance_km: float | None = Field(default=None, ge=0)
    pf_applicable: YesNo | None = None
    esi_applicable: YesNo | None = None
    notice_period_days: int | None = Field(default=None, ge=0)
    exit_date: date | None = None
    resignation_date: date | None = None
    exit_type: str | None = None
    exit_reason: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def _name(cls, value):
        return None if value is None else clean_name(value)

    @field_validator("work_email")
    @classmethod
    def _email(cls, value):
        return None if value is None else clean_email(value)

    @field_validator("hire_date")
    @classmethod
    def _hire_date(cls, value):
        return None if value is None else check_hire_date(value)


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: str
    first_name: str
    last_name: str
    full_name: str
    work_email: str
    gender: str
    date_of_birth: date
    hire_date: date
    exit_date: date | None
    employment_status: str
    employment_type: str
    department_id: str
    role_id: str
    manager_id: str | None
    work_location: str
    work_mode: str
    highest_education: str
    prior_experience_years: float
    career_gap_months: int
    commute_distance_km: float
    pf_applicable: str
    esi_applicable: str
    notice_period_days: int
    resignation_date: date | None
    exit_type: str | None
    exit_reason: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime