"""Add room_day comment column

Revision ID: 0a4525bcdddc
Revises: b20c3b486b36
Create Date: 2022-07-30 20:58:42.128089

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0a4525bcdddc'
down_revision = 'b20c3b486b36'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('room_day',
        sa.Column('comment', sa.TEXT(), nullable=False, server_default="")
    )

def downgrade():
    op.drop_column('room_day', 'comment')
