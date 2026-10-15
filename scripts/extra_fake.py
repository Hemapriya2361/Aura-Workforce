"""50 extra employees made with Faker, kept apart from the master dataset.

The seed adds them only when you ask for them (--with-extra). The same seed
(2026) gives the same people every time.
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from faker import Faker

SEED = 2026
EMAIL_DOMAIN = "znova-demo.example"  # same fake domain the master dataset uses


def _next_id_number(employees: list[dict]) -> int:
    return max(int(e["employee_id"].split("-")[1]) for e in employees) + 1


def _pick_manager(rng, employees, role_level, department_id, level):
    """An active person in the same department, at a higher level than the new hire."""
    candidates = [
        e for e in employees
        if e["is_active"]
        and e["department_id"] == department_id
        and role_level[e["role_id"]] > level
    ]
    if not candidates:
        return None
    # prefer the closest level above, so juniors do not report straight to the CEO
    closest = min(role_level[e["role_id"]] for e in candidates)
    return rng.choice([e for e in candidates if role_level[e["role_id"]] == closest])["employee_id"]


def make_extra_employees(
    employees: list[dict], roles: list[dict], today: date, count: int = 50
) -> list[dict]:
    """Return `count` new employee rows. `employees` and `roles` are the loaded master rows."""
    Faker.seed(SEED)
    fake = Faker("en_IN")
    rng = random.Random(SEED)

    role_level = {r["role_id"]: r["level"] for r in roles}
    junior_roles = [r for r in roles if r["level"] <= 3]
    used_emails = {e["work_email"] for e in employees}
    number = _next_id_number(employees)

    # draw values from the real data, so the extras look like the rest of the company
    genders = [e["gender"] for e in employees]
    locations = [e["work_location"] for e in employees]
    modes = [e["work_mode"] for e in employees]
    educations = [e["highest_education"] for e in employees]

    new_people = []
    for _ in range(count):
        role = rng.choice(junior_roles)
        level = role["level"]
        gender = rng.choice(genders)
        first = fake.first_name_female() if gender == "Female" else fake.first_name_male()
        last = fake.last_name()

        base = f"{first}.{last}".lower().replace(" ", "")
        email, n = f"{base}@{EMAIL_DOMAIN}", 1
        while email in used_emails:
            n += 1
            email = f"{base}{n}@{EMAIL_DOMAIN}"
        used_emails.add(email)

        hire_date = date(2026, 4, 1) + timedelta(days=rng.randint(0, (today - date(2026, 4, 1)).days))
        age = rng.randint(22, 40)
        dob = hire_date.replace(year=hire_date.year - age) - timedelta(days=rng.randint(0, 300))
        experience = {1: (0, 3), 2: (2, 6), 3: (5, 10)}[level]

        person = {
            "employee_id": f"EMP-{number:04d}",
            "first_name": first,
            "last_name": last,
            "full_name": f"{first} {last}",
            "work_email": email,
            "gender": gender,
            "date_of_birth": dob,
            "hire_date": hire_date,
            "exit_date": None,
            "employment_status": "Active",
            "employment_type": "Permanent",
            "department_id": role["department_id"],
            "role_id": role["role_id"],
            "manager_id": _pick_manager(rng, employees, role_level, role["department_id"], level),
            "work_location": rng.choice(locations),
            "work_mode": rng.choice(modes),
            "highest_education": rng.choice(educations),
            "prior_experience_years": Decimal(str(round(rng.uniform(*experience), 1))),
            "career_gap_months": rng.choice([0, 0, 0, 0, 0, 3, 6, 12]),
            "commute_distance_km": Decimal(str(round(rng.uniform(2, 30), 1))),
            "pf_applicable": "Y",
            "esi_applicable": "N",
            "notice_period_days": 30 if level <= 2 else 60,
            "resignation_date": None,
            "exit_type": None,
            "exit_reason": None,
            "is_active": True,
        }
        created = datetime.combine(hire_date - timedelta(days=rng.randint(3, 10)), datetime.min.time())
        person["created_at"] = person["updated_at"] = created
        new_people.append(person)
        number += 1

    return new_people