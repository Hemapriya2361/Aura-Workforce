import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, Department, Role


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add(Department(
            department_id="D01", department_name="Engineering",
            cost_center="CC-100", description="Product engineering"))
        session.add(Role(
            role_id="R002", department_id="D01",
            role_title="Associate Software Engineer", level=1,
            grade="L1 Associate", band_min_annual=400000,
            band_mid_annual=500000, band_max_annual=650000,
            overtime_eligible="N", band_year=2026))
        session.commit()
        yield session