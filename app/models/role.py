from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    department_id: Mapped[str] = mapped_column(
        ForeignKey("departments.department_id"), index=True
    )
    role_title: Mapped[str] = mapped_column(String(120))
    level: Mapped[int] = mapped_column(Integer)
    grade: Mapped[str] = mapped_column(String(60))
    band_min_annual: Mapped[float] = mapped_column(Numeric(12, 2))
    band_mid_annual: Mapped[float] = mapped_column(Numeric(12, 2))
    band_max_annual: Mapped[float] = mapped_column(Numeric(12, 2))
    overtime_eligible: Mapped[str] = mapped_column(String(1))
    band_year: Mapped[int] = mapped_column(Integer)

    department = relationship("Department", back_populates="roles")
    employees = relationship("Employee", back_populates="role")