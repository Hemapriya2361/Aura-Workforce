from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Department(Base):
    __tablename__ = "departments"

    department_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    department_name: Mapped[str] = mapped_column(String(100), unique=True)
    cost_center: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(255))

    roles = relationship("Role", back_populates="department")
    employees = relationship("Employee", back_populates="department")