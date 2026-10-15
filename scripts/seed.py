"""Fill the database from the master dataset (workbook 01).

    python -m scripts.seed --reset                # wipe, then load (the normal first run)
    python -m scripts.seed                        # safe to repeat: adds only what is missing
    python -m scripts.seed --reset --with-extra   # also add the 50 Faker employees

Loads departments, roles and employees. Later tasks add their own tables to LOADERS.
"""
import argparse
import sys
from datetime import date, datetime
from decimal import Decimal

import pandas as pd
from sqlalchemy import delete, func, insert, inspect, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models import Base, Department, Employee, Role
from scripts.export_sheets import csv_path, ensure_csvs
from scripts.extra_fake import make_extra_employees


# ---------- reading the master data ----------

def read_sheet(name: str) -> list[dict]:
    """Rows of one sheet as dicts of text. Empty cells become None."""
    ensure_csvs([name])
    df = pd.read_csv(csv_path(name), dtype=str, keep_default_na=False)
    return [{k: (v if v != "" else None) for k, v in row.items()} for row in df.to_dict("records")]


def _date(value):
    return date.fromisoformat(value) if value else None


def department_row(r: dict) -> dict:
    return dict(r)


def role_row(r: dict) -> dict:
    return {
        **r,
        "level": int(r["level"]),
        "band_min_annual": Decimal(r["band_min_annual"]),
        "band_mid_annual": Decimal(r["band_mid_annual"]),
        "band_max_annual": Decimal(r["band_max_annual"]),
        "band_year": int(r["band_year"]),
    }


def employee_row(r: dict) -> dict:
    created = datetime.fromisoformat(r["created_at"])
    return {
        **r,
        "date_of_birth": _date(r["date_of_birth"]),
        "hire_date": _date(r["hire_date"]),
        "exit_date": _date(r["exit_date"]),
        "resignation_date": _date(r["resignation_date"]),
        "prior_experience_years": Decimal(r["prior_experience_years"]),
        "career_gap_months": int(r["career_gap_months"]),
        "commute_distance_km": Decimal(r["commute_distance_km"]),
        "notice_period_days": int(r["notice_period_days"]),
        "is_active": r["employment_status"] == "Active",
        "created_at": created,
        "updated_at": created,
    }


# ---------- writing ----------

def insert_missing(db: Session, model, rows: list[dict], key: str) -> tuple[int, int]:
    """Insert rows whose key is not in the table yet. Returns (inserted, skipped)."""
    existing = set(db.scalars(select(getattr(model, key))))
    new_rows = [r for r in rows if r[key] not in existing]
    if new_rows:
        db.execute(insert(model), new_rows)
    return len(new_rows), len(rows) - len(new_rows)


def insert_employees(db: Session, rows: list[dict]) -> tuple[int, int]:
    """Two passes: a manager may appear later in the list than the person who reports to them,
    so first insert everyone without a manager, then fill manager_id in."""
    existing = set(db.scalars(select(Employee.employee_id)))
    new_rows = [r for r in rows if r["employee_id"] not in existing]

    # pass 1: everyone, no manager yet
    if new_rows:
        db.execute(insert(Employee), [{**r, "manager_id": None} for r in new_rows])

    # pass 2: the manager links (updated_at is given so it is not overwritten with "now")
    links = [
        {"employee_id": r["employee_id"], "manager_id": r["manager_id"], "updated_at": r["updated_at"]}
        for r in new_rows if r["manager_id"]
    ]
    if links:
        db.execute(update(Employee), links)
    return len(new_rows), len(rows) - len(new_rows)


def wipe(db: Session) -> None:
    """Empty every table, children before parents."""
    db.execute(update(Employee).values(manager_id=None))  # break the self-link first
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(delete(table))


def run_seed(db: Session, reset: bool = False, with_extra: bool = False) -> dict:
    """Load the data. Returns the number of rows expected in each table."""
    if reset:
        wipe(db)
        print("Reset: all tables emptied")

    departments = [department_row(r) for r in read_sheet("departments")]
    roles = [role_row(r) for r in read_sheet("roles")]
    employees = [employee_row(r) for r in read_sheet("employees")]
    expected = {"departments": len(departments), "roles": len(roles), "employees": len(employees)}

    if with_extra:
        extras = make_extra_employees(employees, roles, today=settings.demo_today)
        employees += extras
        expected["employees"] += len(extras)

    for name, model, key, rows in [
        ("departments", Department, "department_id", departments),
        ("roles", Role, "role_id", roles),
    ]:
        inserted, skipped = insert_missing(db, model, rows, key)
        print(f"{name:<12} inserted {inserted:>5}  skipped {skipped:>5}")
    inserted, skipped = insert_employees(db, employees)
    print(f"{'employees':<12} inserted {inserted:>5}  skipped {skipped:>5}")

    db.commit()
    return expected


# ---------- checking ----------

def verify(db: Session, expected: dict) -> list[tuple[str, str, bool]]:
    """Row counts against the sheets, plus a few sanity checks. Returns (check, detail, passed)."""
    results = []
    for name, model in [("departments", Department), ("roles", Role), ("employees", Employee)]:
        count = db.scalar(select(func.count()).select_from(model))
        results.append((f"{name} row count", f"sheet {expected[name]}, database {count}", count == expected[name]))

    def count_where(*conditions) -> int:
        return db.scalar(select(func.count()).select_from(Employee).where(*conditions))

    active = count_where(Employee.is_active.is_(True))
    expected_active = 441 + (expected["employees"] - 745)
    results.append(("active employees", f"{active} (expected {expected_active})", active == expected_active))

    bad_exit = count_where(Employee.exit_date < Employee.hire_date)
    results.append(("no exit before hire", f"{bad_exit} violations", bad_exit == 0))

    active_with_exit = count_where(Employee.is_active.is_(True), Employee.exit_date.is_not(None))
    left_without_exit = count_where(Employee.is_active.is_(False), Employee.exit_date.is_(None))
    results.append(("exit date matches status", f"{active_with_exit + left_without_exit} violations",
                    active_with_exit + left_without_exit == 0))

    manager_ids = select(Employee.employee_id)
    orphans = count_where(Employee.manager_id.is_not(None), Employee.manager_id.not_in(manager_ids))
    self_managed = count_where(Employee.manager_id == Employee.employee_id)
    results.append(("managers exist, none self-managed", f"{orphans + self_managed} violations",
                    orphans + self_managed == 0))

    placeholders = count_where(
        func.lower(Employee.work_email).like("%test%") | func.lower(Employee.full_name).like("%test%")
    )
    results.append(("no placeholder data", f"{placeholders} rows with 'test'", placeholders == 0))
    return results


def print_report(results: list[tuple[str, str, bool]]) -> bool:
    print("\nChecks")
    for check, detail, passed in results:
        print(f"  [{'PASS' if passed else 'FAIL'}] {check:<36} {detail}")
    ok = all(passed for _, _, passed in results)
    print("\nAll checks passed." if ok else "\nSome checks failed. Try again with --reset.")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed the database from the master dataset.")
    parser.add_argument("--reset", action="store_true", help="empty all tables first")
    parser.add_argument("--with-extra", action="store_true", help="also add 50 Faker employees")
    args = parser.parse_args()

    if not inspect(engine).has_table("employees"):
        print("The tables do not exist yet. Run:  alembic upgrade head")
        return 1

    with SessionLocal() as db:
        expected = run_seed(db, reset=args.reset, with_extra=args.with_extra)
        return 0 if print_report(verify(db, expected)) else 1


if __name__ == "__main__":
    sys.exit(main())