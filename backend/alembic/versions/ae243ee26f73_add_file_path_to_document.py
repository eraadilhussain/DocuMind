"""Add file_path to document

Revision ID: ae243ee26f73
Revises: e840d4fbe130
Create Date: 2026-09-12 19:49:59.492056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae243ee26f73'
down_revision: Union[str, Sequence[str], None] = 'e840d4fbe130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('document', sa.Column('file_path', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('document', 'file_path')
