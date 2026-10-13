"""add employee constraints and indexes

Revision ID: 35fc0e412085
Revises: 5a1e10a05b82
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "35fc0e412085"
down_revision: Union[str, Sequence[str], None] = "5a1e10a05b82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        op.f("ix_employees_employment_status"),
        "employees",
        ["employment_status"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_employees_exit_date_after_hire_date",
        "employees",
        "exit_date IS NULL OR exit_date >= hire_date",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_employees_exit_date_after_hire_date",
        "employees",
        type_="check",
    )
    op.drop_index(
        op.f("ix_employees_employment_status"),
        table_name="employees",
    )
