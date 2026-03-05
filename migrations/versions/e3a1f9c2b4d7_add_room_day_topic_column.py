"""Add room_day topic column

Revision ID: e3a1f9c2b4d7
Revises: 0a4525bcdddc
Create Date: 2026-03-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3a1f9c2b4d7'
down_revision = '0a4525bcdddc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('room_day',
        sa.Column('topic', sa.TEXT(), nullable=False, server_default="")
    )

def downgrade():
    op.drop_column('room_day', 'topic')
