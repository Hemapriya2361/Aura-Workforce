from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Employee


def make_employee(emp_id, email, manager_id=None, first_name="Asha"):
    return Employee(
        employee_id=emp_id,
        first_name=first_name,
        last_name="Kumar",
        full_name=f"{first_name} Kumar",
        work_email=email,
        gender="Female",
        date_of_birth=date(1990, 1, 1),
        hire_date=date(2020, 1, 1),
        employment_status="Active",
        employment_type="Permanent",
        department_id="D01",
        role_id="R002",
        manager_id=manager_id,
        work_location="Chennai",
        work_mode="Hybrid",
        highest_education="MCA",
        prior_experience_years=2.0,
        career_gap_months=0,
        commute_distance_km=10.0,
        pf_applicable="Y",
        esi_applicable="N",
        notice_period_days=30,
    )


def test_duplicate_email_fails(db):
    db.add(make_employee("EMP-0001", "asha@example.com"))
    db.commit()
    db.add(make_employee("EMP-0002", "asha@example.com"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_missing_first_name_fails(db):
    emp = make_employee("EMP-0001", "a@example.com")
    emp.first_name = None
    db.add(emp)
    with pytest.raises(IntegrityError):
        db.commit()


def test_manager_hierarchy(db):
    db.add(make_employee("EMP-0001", "boss@example.com", first_name="Boss"))
    db.commit()
    db.add(make_employee("EMP-0002", "a@example.com", manager_id="EMP-0001"))
    db.add(make_employee("EMP-0003", "b@example.com", manager_id="EMP-0001"))
    db.commit()
    boss = db.get(Employee, "EMP-0001")
    assert {e.employee_id for e in boss.direct_reports} == {"EMP-0002", "EMP-0003"}
    assert db.get(Employee, "EMP-0002").manager.employee_id == "EMP-0001"