import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base, Department, Role


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        session.add_all([
            Department(department_id="D01", department_name="Engineering",
                       cost_center="CC-100", description="Product engineering"),
            Department(department_id="D02", department_name="Sales",
                       cost_center="CC-400", description="Enterprise sales"),
        ])
        session.add_all([
            Role(role_id="R002", department_id="D01",
                 role_title="Associate Software Engineer", level=1,
                 grade="L1 Associate", band_min_annual=400000,
                 band_mid_annual=500000, band_max_annual=650000,
                 overtime_eligible="N", band_year=2026),
            Role(role_id="R010", department_id="D02",
                 role_title="Sales Executive", level=2,
                 grade="L2 Executive", band_min_annual=500000,
                 band_mid_annual=600000, band_max_annual=750000,
                 overtime_eligible="N", band_year=2026),
        ])
        session.commit()
    return engine


@pytest.fixture
def db(engine):
    with sessionmaker(bind=engine)() as session:
        yield session


@pytest.fixture
def client(engine):
    session_factory = sessionmaker(bind=engine)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()