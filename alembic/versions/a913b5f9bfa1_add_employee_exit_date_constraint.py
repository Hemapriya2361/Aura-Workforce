"""add employee exit date constraint

Revision ID: a913b5f9bfa1
Revises: 35fc0e412085
Create Date: 2026-10-13 13:56:48.971470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a913b5f9bfa1'
down_revision: Union[str, Sequence[str], None] = '35fc0e412085'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_employees_exit_date_after_hire_date",
        "employees",
        "exit_date IS NULL OR exit_date >= hire_date",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_employees_exit_date_after_hire_date",
        "employees",
        type_="check",
    )
