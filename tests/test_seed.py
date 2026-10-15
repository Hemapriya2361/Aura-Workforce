import csv
from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.models import Base, Department, Employee, Role
from scripts.export_csv import export_dataset
from scripts.extra_fake import make_extra_employees
from scripts.seed import employee_row, read_sheet, role_row, run_seed, verify


@pytest.fixture
def empty_engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def seed_db(empty_engine):
    with sessionmaker(bind=empty_engine)() as session:
        yield session


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_seed_matches_the_sheets(seed_db):
    expected = run_seed(seed_db, reset=True)
    assert (count(seed_db, Department), count(seed_db, Role), count(seed_db, Employee)) == (11, 58, 745)
    assert all(passed for _, _, passed in verify(seed_db, expected))


def test_active_and_left_employees(seed_db):
    run_seed(seed_db, reset=True)
    active = seed_db.scalar(select(func.count()).select_from(Employee).where(Employee.is_active))
    assert active == 441


def test_managers_are_linked(seed_db):
    run_seed(seed_db, reset=True)
    with_manager = seed_db.scalar(
        select(func.count()).select_from(Employee).where(Employee.manager_id.is_not(None))
    )
    assert with_manager > 700
    # EMP-0001 reports to EMP-0002, who appears later in the sheet (the reason for two passes)
    assert seed_db.get(Employee, "EMP-0001").manager_id == "EMP-0002"


def test_running_twice_makes_no_duplicates(seed_db):
    run_seed(seed_db, reset=True)
    run_seed(seed_db)  # second run, no reset
    run_seed(seed_db)
    assert (count(seed_db, Department), count(seed_db, Role), count(seed_db, Employee)) == (11, 58, 745)


def test_running_twice_with_reset_gives_the_same_result(seed_db):
    run_seed(seed_db, reset=True)
    run_seed(seed_db, reset=True)
    assert count(seed_db, Employee) == 745


def test_reset_removes_leftover_rows(seed_db):
    run_seed(seed_db, reset=True)
    seed_db.add(
        Employee(
            employee_id="EMP-9999", first_name="Left", last_name="Over", full_name="Left Over",
            work_email="left.over@znova-demo.example", gender="Male", date_of_birth=date(1990, 1, 1),
            hire_date=date(2026, 1, 1), department_id="D01", role_id="R002", work_location="Pune",
            work_mode="Remote", highest_education="MCA", prior_experience_years=0,
            career_gap_months=0, commute_distance_km=1, pf_applicable="Y", esi_applicable="N",
            notice_period_days=30,
        )
    )
    seed_db.commit()
    run_seed(seed_db, reset=True)
    assert seed_db.get(Employee, "EMP-9999") is None


def test_seed_keeps_the_sheet_dates(seed_db):
    run_seed(seed_db, reset=True)
    first = seed_db.get(Employee, "EMP-0001")
    assert first.hire_date == date(2012, 1, 19)
    assert first.exit_date == date(2020, 1, 24)
    assert first.is_active is False


# ---------- the 50 Faker employees ----------

def extra_people():
    employees = [employee_row(r) for r in read_sheet("employees")]
    roles = [role_row(r) for r in read_sheet("roles")]
    return employees, roles, make_extra_employees(employees, roles, today=settings.demo_today)


def test_extra_employees_are_the_same_every_time():
    assert extra_people()[2] == extra_people()[2]


def test_extra_employees_are_valid():
    employees, roles, extras = extra_people()
    assert len(extras) == 50
    assert extras[0]["employee_id"] == "EMP-0746" and extras[-1]["employee_id"] == "EMP-0795"
    emails = [e["work_email"] for e in employees + extras]
    assert len(emails) == len(set(emails))
    ids = {e["employee_id"] for e in employees}
    for person in extras:
        assert person["hire_date"] <= settings.demo_today
        assert person["department_id"] in {r["department_id"] for r in roles}
        assert person["manager_id"] is None or person["manager_id"] in ids
        assert person["work_email"].endswith("@znova-demo.example")
        assert "test" not in person["full_name"].lower()


def test_seed_with_extra(seed_db):
    expected = run_seed(seed_db, reset=True, with_extra=True)
    assert count(seed_db, Employee) == 795
    assert all(passed for _, _, passed in verify(seed_db, expected))
    run_seed(seed_db, with_extra=True)  # again, still 795
    assert count(seed_db, Employee) == 795


# ---------- CSV export ----------

def test_export_employees_csv(seed_db, empty_engine, tmp_path):
    run_seed(seed_db, reset=True)
    rows, source = export_dataset("employees", empty_engine, tmp_path)
    assert (rows, source) == (745, "database")
    with open(tmp_path / "employees.csv", newline="", encoding="utf-8") as f:
        records = list(csv.DictReader(f))
    assert len(records) == 745
    assert records[0]["employee_id"] == "EMP-0001"
    assert records[0]["hire_date"] == "2012-01-19"


def test_export_rejects_unknown_dataset(empty_engine, tmp_path):
    with pytest.raises(ValueError):
        export_dataset("users; drop table employees", empty_engine, tmp_path)